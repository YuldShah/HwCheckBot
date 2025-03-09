import logging
import psycopg2
import json
from psycopg2 import sql, DatabaseError

# Configure logging as needed
logging.basicConfig(level=logging.INFO)


class DatabaseManager:
    def __init__(self, DB_URL):
        """
        Initialize connection to the database.
        """
        try:
            self.conn = psycopg2.connect(DB_URL)
        except DatabaseError:
            logging.error("Database connection error", exc_info=True)
            raise

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
            )"""
        ]
        for query in queries:
            self.query(query)

    def query(self, arg, values=None):
        """Execute a query that does not return results."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(arg, values or ())
                self.conn.commit()
        except DatabaseError:
            self.conn.rollback()
            logging.error("Query error", exc_info=True)

    def fetchone(self, arg, values=None):
        """Execute a query and return a single result."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(arg, values or ())
                return cur.fetchone()
        except DatabaseError:
            self.conn.rollback()
            logging.error("FetchOne error", exc_info=True)
            return None

    def fetchall(self, arg, values=None):
        """Execute a query and return all results."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(arg, values or ())
                return cur.fetchall()
        except DatabaseError:
            self.conn.rollback()
            logging.error("FetchAll error", exc_info=True)
            return None

    def get_tables(self):
        """Return a list of all table names in the public schema."""
        tables = self.fetchall("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';")
        return [table[0] for table in tables] if tables else []

    def execute_sql(self, query, values=None):
        """Execute any SQL query with optional parameters and return results if applicable."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values or ())
                if query.strip().lower().startswith("select"):
                    return cur.fetchall()
                self.conn.commit()
                return "Query executed successfully."
        except DatabaseError:
            self.conn.rollback()
            logging.error("SQL Execution error", exc_info=True)
            return None

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

    def close(self):
        """Close the connection properly."""
        if self.conn:
            self.conn.close()

    def __del__(self):
        """Ensure cleanup when the object is destroyed."""
        self.close()
