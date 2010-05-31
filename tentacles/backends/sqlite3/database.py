
from tentacles import Object
from tentacles.fields import Reference, ReferenceSet

REFORDER = 1


class SQLiteStorage(object):
	def __init__(self, uri):
		self.db = sqlite3.connect(uri.db)
		self.db.row_factory = sqlite3.Row

		self.cursor = self.db.cursor()

	def execute(self, query, args=()):
		res = self.cursor.execute(query, args)

		return self.cursor.lastrowid

	def query(self, query, args=()):
		self.cursor.execute(query, args)
		return self.cursor.fetchall()

	def create(self):
		for obj in self.__objects__:
			q = obj.create()
			self.execute(q)
