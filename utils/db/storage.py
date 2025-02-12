import psycopg2
from psycopg2 import sql, DatabaseError

class DatabaseManager:
    def __init__(self, DB_URL):
        try:
            self.conn = psycopg2.connect(DB_URL, sslmode="require")
            self.cur = self.conn.cursor()
        except DatabaseError as e:
            print(f"Database connection error: {e}")
            raise

    def create_tables(self):
        try:
            self.query('''CREATE TABLE IF NOT EXISTS users (idx SERIAL PRIMARY KEY, userid TEXT, fullname TEXT, username TEXT, regdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP, allowed INTEGER DEFAULT 0)''')
            self.query("CREATE TABLE IF NOT EXISTS folders (idx SERIAL PRIMARY KEY, title TEXT)")
            self.query("CREATE TABLE IF NOT EXISTS exams (idx SERIAL PRIMARY KEY, title TEXT, about TEXT DEFAULT NULL, instructions TEXT, num_questions INTEGER, correct TEXT, sdate TEXT DEFAULT NULL, resub INTEGER DEFAULT 1, folder INTEGER DEFAULT NULL, hide INTEGER DEFAULT 0, random TEXT)")
            self.query("CREATE TABLE IF NOT EXISTS submissions(idx SERIAL PRIMARY KEY, userid TEXT, exid INTEGER, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, answers TEXT)")
            self.query("CREATE TABLE IF NOT EXISTS channel (idx SERIAL PRIMARY KEY, chid TEXT, title TEXT, link TEXT)")
            self.query("CREATE TABLE IF NOT EXISTS jobs (idx SERIAL PRIMARY KEY, type TEXT, data TEXT DEFAULT NULL, run TIMESTAMP NOT NULL, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, completed INTEGER DEFAULT 0)")
            self.query("CREATE TABLE IF NOT EXISTS attachments (idx SERIAL PRIMARY KEY, tgfileid TEXT DEFAULT NULL, caption TEXT DEFAULT NULL, exid INTEGER DEFAULT NULL)")
        except DatabaseError as e:
            print(f"Error creating tables: {e}")

    def query(self, arg, values=None):
        try:
            self.cur.execute(arg, values or ())
            self.conn.commit()
        except DatabaseError as e:
            self.conn.rollback()
            print(f"Query error: {e}")

    def fetchone(self, arg, values=None):
        try:
            self.cur.execute(arg, values or ())
            return self.cur.fetchone()
        except DatabaseError as e:
            self.conn.rollback()
            print(f"FetchOne error: {e}")
            return None

    def fetchall(self, arg, values=None):
        try:
            self.cur.execute(arg, values or ())
            return self.cur.fetchall()
        except DatabaseError as e:
            self.conn.rollback()
            print(f"FetchAll error: {e}")
            return None

    def get_tables(self):
        try:
            tables = self.fetchall("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';")
            return [table[0] for table in tables] if tables else []
        except DatabaseError as e:
            print(f"Error fetching tables: {e}")
            return []

    def execute_sql(self, query):
        try:
            self.cur.execute(query)
            if query.strip().lower().startswith("select"):
                return self.fetchall(query)
            else:
                self.conn.commit()
                return "Query executed successfully."
        except DatabaseError as e:
            self.conn.rollback()
            print(f"SQL Execution error: {e}")
            return None

    def get_last_n_rows(self, table, n):
        try:
            self.cur.execute(sql.SQL("SELECT * FROM {} ORDER BY idx DESC LIMIT %s").format(sql.Identifier(table)), (n,))
            return self.cur.fetchall()
        except DatabaseError as e:
            self.conn.rollback()
            print(f"SQL Error fetching last {n} rows from {table}: {e}")
            return None

    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            self.cur.close()
            self.conn.close()
