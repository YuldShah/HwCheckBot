import json
import logging

import psycopg2
from psycopg2 import DatabaseError, InterfaceError, OperationalError, sql
from psycopg2.pool import SimpleConnectionPool

# Configure logging as needed
logging.basicConfig(level=logging.INFO)


class DatabaseManager:
    def __init__(self, DB_URL):
        """
        Initialize connection to the database.
        """
        try:
            self.db_url = DB_URL
            self.pool = SimpleConnectionPool(1, 5, DB_URL)
        except DatabaseError:
            logging.error("Database connection error", exc_info=True)
            raise

    def _get_connection(self):
        if self.pool is None:
            raise InterfaceError("connection pool is closed")

        conn = self.pool.getconn()
        if conn.closed:
            self.pool.putconn(conn, close=True)
            conn = self.pool.getconn()
        conn.autocommit = True
        return conn

    def _release_connection(self, conn, close=False):
        if self.pool is None or conn is None:
            return
        self.pool.putconn(conn, close=close or bool(conn.closed))

    def _execute(self, query, values=None, fetch=None, retry=True):
        conn = None
        params = () if values is None else values

        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(query, params)
                if fetch == "one":
                    return cur.fetchone()
                if fetch == "all":
                    return cur.fetchall()
                return True
        except (InterfaceError, OperationalError):
            if conn is not None:
                self._release_connection(conn, close=True)
                conn = None
            logging.warning("Database connection lost, retrying once", exc_info=True)
            if retry:
                return self._execute(query, values=values, fetch=fetch, retry=False)
            logging.error("Database operation failed after reconnect attempt", exc_info=True)
            return None
        except DatabaseError:
            logging.error("Database operation error", exc_info=True)
            return None
        finally:
            if conn is not None:
                self._release_connection(conn)

    def create_tables(self):
        """Create necessary tables if they do not exist."""
        queries = [
            """CREATE TABLE IF NOT EXISTS users (
                idx SERIAL PRIMARY KEY, 
                userid TEXT, 
                fullname TEXT, 
                username TEXT, 
                regdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                allowed INTEGER DEFAULT 0, 
                arch INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS folders (idx SERIAL PRIMARY KEY, title TEXT)""",
            """CREATE TABLE IF NOT EXISTS exams (
                idx SERIAL PRIMARY KEY, 
                title TEXT, 
                about TEXT DEFAULT NULL, 
                instructions TEXT, 
                num_questions INTEGER, 
                correct TEXT, 
                sdate TIMESTAMP, 
                resub INTEGER DEFAULT 0, 
                folder INTEGER DEFAULT 0, 
                hide INTEGER DEFAULT 0, 
                random TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS submissions (
                idx SERIAL PRIMARY KEY, 
                userid TEXT, 
                exid INTEGER, 
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                answers TEXT, 
                random TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS channel (idx SERIAL PRIMARY KEY, chid TEXT, title TEXT, link TEXT)""",
            """CREATE TABLE IF NOT EXISTS attachments (
                idx SERIAL PRIMARY KEY, 
                ty TEXT DEFAULT NULL, 
                tgfileid TEXT DEFAULT NULL, 
                caption TEXT DEFAULT NULL, 
                exid INTEGER DEFAULT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS scheduled_tasks (
                idx SERIAL PRIMARY KEY,
                user_id TEXT,
                task_name TEXT NOT NULL,
                task_data TEXT,
                run_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed INTEGER DEFAULT 0
            )"""
        ]
        for query in queries:
            self.query(query)

    def query(self, arg, values=None):
        """Execute a query that does not return results."""
        self._execute(arg, values=values)

    def fetchone(self, arg, values=None):
        """Execute a query and return a single result."""
        return self._execute(arg, values=values, fetch="one")

    def fetchall(self, arg, values=None):
        """Execute a query and return all results."""
        return self._execute(arg, values=values, fetch="all")

    def get_tables(self):
        """Return a list of all table names in the public schema."""
        tables = self.fetchall("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';")
        return [table[0] for table in tables] if tables else []

    def execute_sql(self, query, values=None):
        """Execute any SQL query with optional parameters and return results if applicable."""
        fetch_mode = "all" if query.strip().lower().startswith("select") else None
        result = self._execute(query, values=values, fetch=fetch_mode)
        if fetch_mode == "all":
            return result
        return "Query executed successfully." if result else None

    def store_submission(self, userid, exid, answers, code, sub_time):
        """Store a submission in the database."""
        answers = json.dumps(answers)
        try:
            self.query(
                "INSERT INTO submissions(userid, exid, answers, random, date) VALUES (%s, %s, %s, %s, %s)", 
                (userid, exid, answers, code, sub_time)
            )
            return True
        except Exception:
            logging.error("Error storing submission", exc_info=True)
            return False

    def get_last_n_rows(self, table, n):
        """Retrieve the last n rows from the specified table."""
        try:
            return self.fetchall(
                sql.SQL("SELECT * FROM {} ORDER BY idx DESC LIMIT %s").format(sql.Identifier(table)), 
                (n,)
            )
        except DatabaseError:
            logging.error(f"SQL Error fetching last {n} rows from {table}", exc_info=True)
            return None

    def get_due_tasks(self):
        """Return all pending scheduled tasks whose run_at time has passed."""
        return self.fetchall(
            "SELECT idx, user_id, task_name, task_data, run_at, created_at, completed "
            "FROM scheduled_tasks WHERE completed = 0 AND run_at <= NOW()"
        ) or []

    def mark_task_completed(self, task_id):
        """Mark a scheduled task as completed."""
        self.query("UPDATE scheduled_tasks SET completed = 1 WHERE idx = %s", (task_id,))

    def schedule_task(self, user_id, task_name, task_data, run_at):
        """Insert a new scheduled task."""
        self.query(
            "INSERT INTO scheduled_tasks (user_id, task_name, task_data, run_at) VALUES (%s, %s, %s, %s)",
            (user_id, task_name, task_data, run_at)
        )

    def close(self):
        """Close the connection properly."""
        if self.pool:
            self.pool.closeall()
            self.pool = None

    def __del__(self):
        """Ensure cleanup when the object is destroyed."""
        self.close()
