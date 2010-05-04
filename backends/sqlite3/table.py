import inspect, types, StringIO, sqlite3
from tentacles.fields import Reference


class Object(object):
	sqlite3 = None

	def __init__(self, *args, **kwargs):
		pass

	@classmethod
	def create(cls):
		q = 'CREATE TABLE ' + cls.__stor_name__ + ' ( \n'
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
			if not fld.none:
				q += " NOT NULL"
			if hasattr(fld, '__default__'):
				q += " DEFAULT"
				if fld.default() is None:
					q += " NULL"
				else:
					q += " " + fld.sql_protect(fld.default())

			q += ",\n"

		if len(cls.__pk__) > 1:
			q += "\n PRIMARY KEY ("
			for pk in cls.__pk__:
				q += pk.name + ', '
			q = q[:-2] + '),\n'
			
#		if hasattr(cls, '__refs__'):
#		    for table, refs in cls.__refs__.iteritems():
#		        if len(refs) < 2:
#		            continue
#		        
#		        q += ' FOREIGN KEY ('
#		        for local, remote in refs:
#		            q += "%s, " % local.name
#		        q = q[:-2] + ') REFERENCES %s (' % table.__table_name__
#		        for local, remote in refs:
#		            q += "%s, " % remote.name
#		        q = q[:-2] + '),\n'
		q = q[:-2] + '\n)'
		return q

	def save(self):
		if len(self.__changes__) == 0:
			return

		# check references
		for refdef in self.__references__:
			refval = getattr(self, refdef.name)
			if refval and not isinstance(refval, ReferenceList) and not refval.saved():
				refval.save()

		fields = filter(lambda x: not isinstance(x, ReferenceList), self.__changes__.values())
		rels   = filter(lambda x: isinstance(x, ReferenceList), self.__changes__.values())
#		print '!!',self.__table_name__, self.__changes__, fields, rels
		
		if len(fields) > 0:
			if self.__saved__:
				q, values = self._update()
			else:
				q, values = self._insert()
				self.__dict__['__saved__'] = True

			print q, values
			
		if len(rels) > 0:
			for rel in rels:
				rel.save()
			
		self.__changes__.clear()

	def _insert(self):
		values = []
		q = 'INSERT INTO %s VALUES(' % self.__table_name__
		for name, fld in self.__fields__.iteritems():
			if fld.__hidden__:
				continue

			q += '?, '
			value = getattr(self, name)
			if value is None:
			    value = 'NULL'
			values.append(value)
		q = q[:-2] + ')'

#		q = 'INSERT INTO %s VALUES(' % self.__table_name__
#		for name, fld in self.__fields__.iteritems():
#			if fld.__hidden__:
#				continue

#			q += "?, "
#			values.append(getattr(self, name))
#		q = q[:-2] + ')'

		return q, values

	def _update(self):
		values = []
		q = 'UPDATE TABLE %s SET ' % self.__table_name__

		for name, value in self.__changes__.iteritems():
			if isinstance(value, ReferenceList):
				continue

			q += "%s = ?, " % name

			if isinstance(self.__fields__[name], Reference):
				value = getattr(value, value.__pk__[0].name)
			values.append(value)
		q = q[:-2] + ' WHERE '

		for pk in self.__pk__:
			q += "%s = ? AND " % pk.name
			values.append(self.__origin__[pk.name])
			self.__origin__[pk.name] = getattr(self, pk.name)

		q = q[:-4]
		return q, values
