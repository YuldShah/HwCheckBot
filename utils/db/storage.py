import psycopg2
from psycopg2 import sql

class DatabaseManager:
    def __init__(self, DB_URL):
        self.conn = psycopg2.connect(DB_URL, sslmode="require")
        self.cur = self.conn.cursor()

    def create_tables(self):
        self.query('''CREATE TABLE IF NOT EXISTS users (idx SERIAL PRIMARY KEY, userid TEXT, fullname TEXT, username TEXT, regdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP, allowed INTEGER DEFAULT 0)''')
        self.query("CREATE TABLE IF NOT EXISTS folders (idx SERIAL PRIMARY KEY, title TEXT)")
        self.query("CREATE TABLE IF NOT EXISTS exams (idx SERIAL PRIMARY KEY, title TEXT, about TEXT DEFAULT NULL, instructions TEXT, num_questions INTEGER, correct TEXT, sdate TEXT DEFAULT NULL, resub INTEGER DEFAULT 1, folder INTEGER DEFAULT NULL, hide INTEGER DEFAULT 0)")
        self.query("CREATE TABLE IF NOT EXISTS submissions(idx SERIAL PRIMARY KEY, userid TEXT, exid INTEGER, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, answers TEXT)")
        self.query("CREATE TABLE IF NOT EXISTS channel (idx SERIAL PRIMARY KEY, chid INTEGER, title TEXT, link TEXT)")

    def query(self, arg, values=None):
        self.cur.execute(arg, values or ())
        self.conn.commit()

    def fetchone(self, arg, values=None):
        self.cur.execute(arg, values or ())
        return self.cur.fetchone()

    def fetchall(self, arg, values=None):
        self.cur.execute(arg, values or ())
        return self.cur.fetchall()

    def get_tables(self):
        """Returns a list of table names in the database."""
        try:
            tables = self.fetchall("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';")
            return [table[0] for table in tables] if tables else []
        except Exception as e:
            print(f"Error fetching tables: {e}")
            return []

    def execute_sql(self, query):
        """Executes an arbitrary SQL query and returns the result."""
        try:
            self.cur.execute(query)
            if query.strip().lower().startswith("select"):
                return self.fetchall(query)
            else:
                self.conn.commit()
                return "Query executed successfully."
        except Exception as e:
            return f"SQL Error: {e}"

    def get_last_n_rows(self, table, n):
        """Fetches the last N rows from a given table."""
        try:
            self.cur.execute(sql.SQL("SELECT * FROM {} ORDER BY idx DESC LIMIT %s").format(sql.Identifier(table)), (n,))
            return self.cur.fetchall()
        except Exception as e:
            return f"SQL Error: {e}"

    def __del__(self):
        self.conn.close()


"""
exams: idx, title, about, instructions, num_questions, correct, sdate, duration, resub, folder, hide
"""