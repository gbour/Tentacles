import sqlite3

class SQLiteDatabase(object):
    def __init__(self, uri):
        self.uri = uri
        self.db = sqlite3.connect(uri.db)
        print '>>',self.db
        
    def toto(self):
        print "SQLiteDatabase::toto"
        
    def execute(self, query):
        res = self.db.execute(query)
