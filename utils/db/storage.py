import sqlite3 as lite


class DatabaseManager(object):

    def __init__(self, path):
        self.conn = lite.connect(path)
        self.conn.execute('pragma foreign_keys = on')
        self.conn.commit()
        self.cur = self.conn.cursor()



    def create_tables(self):
        self.query('CREATE TABLE IF NOT EXISTS users (idx INTEGER PRIMARY KEY, userid TEXT, fullname TEXT, username TEXT, regdate TEXT DEFAULT CURRENT_TIMESTAMP)')
        self.query("CREATE TABLE IF NOT EXISTS folders (idx INTEGER PRIMARY KEY, title TEXT)")
        self.query("CREATE TABLE IF NOT EXISTS messages (idx INTEGER PRIMARY KEY, jid INTEGER, msgid TEXT DEFAULT NULL, status INTEGER DEFAULT 0, date TEXT)")
        self.query("CREATE TABLE IF NOT EXISTS exams (idx INTEGER PRIMARY KEY, code TEXT, title TEXT, about TEXT DEFAULT NULL, num_questions INTEGER, correct TEXT, folder INTEGER DEFUALT NULL, sdate TEXT DEFAULT NULL, duration INTEGER DEFAULT NULL, running INTEGER DEFAULT 0, hide INTEGER DEFAULT 1)")
        self.query("CREATE TABLE IF NOT EXISTS submissions(idx INTEGER PRIMARY KEY, exid INTEGER, userid TEXT, date TEXT DEFAULT CURRENT_TIMESTAMP, corr INTEGER)")
        self.query("CREATE TABLE IF NOT EXISTS channel (idx INTEGER PRIMARY KEY, chid TEXT, title TEXT, link TEXT, post INTEGER DEFAULT 0)")

    def query(self, arg, values=None):
        if values == None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        self.conn.commit()

    def fetchone(self, arg, values=None):
        if values == None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        return self.cur.fetchone()

    def fetchall(self, arg, values=None):
        if values == None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        return self.cur.fetchall()

    def __del__(self):
        self.conn.close()


'''
users: idx, userid, fullname, username, regdate, banned
exams: idx, code, title, about, num_questions, correct, running
submissions: idx, exid, userid, date, corr
channel: idx, chid, title, username
'''