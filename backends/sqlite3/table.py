import inspect, types, StringIO, sqlite3
from tentacles.fields import Reference


class Table(object):
	sqlite3 = None

	def __init__(self, *args, **kwargs):
		self.zz = 22

	@classmethod
	def create(cls):
		q = 'CREATE TABLE ' + cls.__table_name__ + ' ( \n'
		for fld in cls.__fields__.itervalues():
			if fld.__hidden__:
				continue
			
			q += " " + fld.sql_def()

#			if issubclass(fld.__class__, Reference):
#				q += ",\n"
#				continue

			if len(cls.__pk__) == 1 and fld.pk:
				q += " PRIMARY KEY"
			if fld.unique:
				q += " UNIQUE"
			if fld.notnull:
				q += " NOT NULL"
			if hasattr(fld, 'default'):
				q += " DEFAULT"
				if fld.default is None:
					q += " NULL"
				else:
					q += " " + fld.sql_protect(fld.default)

			q += ",\n"

		if len(cls.__pk__) > 1:
			q += "\n PRIMARY KEY ("
			for pk in cls.__pk__:
				q += pk.name + ','
			q = q[:-1] + '),\n'
			
		if hasattr(cls, '__refs__'):
		    for table, refs in cls.__refs__.iteritems():
		        if len(refs) < 2:
		            continue
		        
		        q += ' FOREIGN KEY ('
		        for local, remote in refs:
		            q += "%s, " % local.name
		        q = q[:-2] + ') REFERENCES %s (' % table.__table_name__
		        for local, remote in refs:
		            q += "%s, " % remote.name
		        q = q[:-2] + '),\n'
		q = q[:-2] + '\n)'
		return q

	def save(self):
		if len(self.__changes__) == 0:
			return

		if self.__saved__:
			q, values = self._update()
		else:
			q, values = self._insert()

		self.__dict__['__saved__'] = True
		self.__changes__.clear()
#		self.__origin__.clear()
		print q, values
		print self.__origin__

	def _insert(self):
		values = []
		q = 'INSERT INTO %s VALUES(' % self.__table_name__
		for name, fld in self.__fields__.iteritems():
			if fld.__hidden__:
				continue

			q += "?, "
			values.append(getattr(self, name))
		q = q[:-2] + ')'

		return q, values

	def _update(self):
		values = []
		q = 'UPDATE TABLE %s SET ' % self.__table_name__
		for name, value in self.__changes__.iteritems():
			q += "%s = ?, " % name
			values.append(value)
		q = q[:-2] + ' WHERE '

		for pk in self.__pk__:
			q += "%s = ? AND" % pk.name
			values.append(self.__origin__[pk.name])
			self.__origin__[pk.name] = value

		q = q[:-4]
		return q, values
