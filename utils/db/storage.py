import logging
import sqlite3 as lite
import json

# Configure logging as needed
logging.basicConfig(level=logging.INFO)

class DatabaseManager:
    def __init__(self, path):
        self.conn = lite.connect(path)
        self.conn.execute('pragma foreign_keys = on')
        self.conn.commit()
        self.cur = self.conn.cursor()

    def create_tables(self):
        """
        Create necessary tables if they do not exist.
        """
        try:
            self.query('''CREATE TABLE IF NOT EXISTS users (idx SERIAL PRIMARY KEY, userid TEXT, fullname TEXT, username TEXT, regdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP, allowed INTEGER DEFAULT 0, arch INTEGER DEFAULT 0)''')
            self.query("CREATE TABLE IF NOT EXISTS folders (idx SERIAL PRIMARY KEY, title TEXT)")
            self.query("CREATE TABLE IF NOT EXISTS exams (idx SERIAL PRIMARY KEY, title TEXT, about TEXT DEFAULT NULL, instructions TEXT, num_questions INTEGER, correct TEXT, sdate TEXT DEFAULT NULL, resub INTEGER DEFAULT 0, folder INTEGER DEFAULT 0, hide INTEGER DEFAULT 0, random TEXT)")
            self.query("CREATE TABLE IF NOT EXISTS submissions (idx SERIAL PRIMARY KEY, userid TEXT, exid INTEGER, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, answers TEXT, random TEXT)")
            self.query("CREATE TABLE IF NOT EXISTS channel (idx SERIAL PRIMARY KEY, chid TEXT, title TEXT, link TEXT)")
            self.query("CREATE TABLE IF NOT EXISTS attachments (idx SERIAL PRIMARY KEY, ty TEXT DEFAULT NULL, tgfileid TEXT DEFAULT NULL, caption TEXT DEFAULT NULL, exid INTEGER DEFAULT NULL)")
        except Exception as e:
            logging.error("Error creating tables", exc_info=True)

    def query(self, arg, values=None):
        """
        Execute a query that does not return results.
        """
        arg.replace("%s", "?")
        try:
            self.cur.execute(arg, values or ())
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logging.error("Query error", exc_info=True)

    def fetchone(self, arg, values=None):
        """
        Execute a query and return a single result.
        """
        arg.replace("%s", "?")
        try:
            self.cur.execute(arg, values or ())
            return self.cur.fetchone()
        except Exception as e:
            self.conn.rollback()
            logging.error("FetchOne error", exc_info=True)
            return None

    def fetchall(self, arg, values=None):
        """
        Execute a query and return all results.
        """
        arg.replace("%s", "?")
        try:
            self.cur.execute(arg, values or ())
            return self.cur.fetchall()
        except Exception as e:
            self.conn.rollback()
            logging.error("FetchAll error", exc_info=True)
            return None

    def get_tables(self):
        """
        Return a list of all table names in the public schema.
        """
        try:
            tables = self.fetchall("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';")
            return [table[0] for table in tables] if tables else []
        except Exception as e:
            logging.error("Error fetching tables", exc_info=True)
            return []

    def execute_sql(self, query):
        """
        Execute any SQL query and return results if applicable.
        """
        try:
            self.cur.execute(query)
            if query.strip().lower().startswith("select"):
                return self.fetchall(query)
            else:
                self.conn.commit()
                return "Query executed successfully."
        except Exception as e:
            self.conn.rollback()
            logging.error("SQL Execution error", exc_info=True)
            return None

    def store_submission(self, userid, exid, answers, code, sub_time):
        """
        Store a submission in the database with the submission time.
        
        Parameters:
        userid: user identifier (str)
        exid: exam/test id (int)
        answers: answers given by the user (list)
        code: submission code (str)
        sub_time: submission timestamp (datetime)
        """
        answers = json.dumps(answers)
        try:
            self.query(
                "INSERT INTO submissions(userid, exid, answers, random, date) VALUES (?, ?, ?, ?, ?)", 
                (userid, exid, answers, code, sub_time)
            )
        except Exception:
            import logging
            logging.error("Error storing submission", exc_info=True)
            return False
        return True

    def get_last_n_rows(self, table, n):
        """
        Retrieve the last n rows from the specified table.
        """
        try:
            self.query("SELECT * FROM {} ORDER BY idx DESC LIMIT ?", (n,))
            return self.cur.fetchall()
        except Exception as e:
            self.conn.rollback()
            logging.error(f"SQL Error fetching last {n} rows from {table}", exc_info=True)
            return None

    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            self.cur.close()
            self.conn.close()
