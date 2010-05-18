import inspect, types, StringIO, sqlite3
from tentacles.fields import Reference, ReferenceSet
from tentacles import Storage, Ghost


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
			if fld.autoincrement:
				q += " AUTOINCREMENT"
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
		if not self.__changed__ or self.__locked__:
			return

		self.__dict__['__locked__'] = True
		# check references
#		print 'SAVE>', self
		for refdef in self.__refs__:
			refval = getattr(self, refdef.name)
#			print 'Zzz.', refdef, refval, type(refval)
			if refval is not None and not refval.saved():
#			if refval and not isinstance(refval, ReferenceList) and not refval.saved():
#				print '  . saving'
				refval.save()

#		fields = filter(lambda x: not isinstance(x, ReferenceList), self.__changes__.values())
#		rels   = filter(lambda x: isinstance(x, ReferenceList), self.__changes__.values())
#		print '!!',self.__table_name__, self.__changes__, fields, rels
		
		if len(self.__changes__) > 0:
			if self.__saved__:
				q, values = self._update()
			else:
				q, values = self._insert()
				self.__dict__['__saved__'] = True

			print q, values
			autoid = Storage.__instance__.execute(q, values)

			if self.__pk__[0].autoincrement:
				setattr(self, self.__pk__[0].name, autoid)

#		print 'refs=', self, self.__refs__
		for refdef in self.__refs__:
			refval = getattr(self, refdef.name)
#			print ' .. ', refdef, refval, type(refval)
#			if refval:
#				print '  haschanged=', refval.has_changed()
			if refval and refval.has_changed():
#			if refval and not isinstance(refval, ReferenceList) and not refval.saved():
#				print 'save', refval, type(refval)
				refval.save()

			if refdef.name in self.__origin__:
				if self.__origin__[refdef.name]:
#					print 'save old', self.__origin__[refdef.name]
					self.__origin__[refdef.name].save()
				self.__origin__[refdef.name] = refval

#		if len(rels) > 0:
#			for rel in rels:
#				rel.save()
			
		self.__changes__.clear()
		self.__dict__['__changed__'] = False
		self.__dict__['__locked__']  = False

	def _insert(self):
		values = []
		q = 'INSERT INTO %s VALUES(' % self.__stor_name__
		for name, fld in self.__fields__.iteritems():
#			if fld.__hidden__:
			if isinstance(fld, ReferenceSet):
				continue

			q += '?, '
			value = getattr(self, name)
			if value is not None and isinstance(fld, Reference):
				value = getattr(value, value.__pk__[0].name)

			# check if it is ok for sqlite
#			if value is None:
#			    value = 'NULL'
			values.append(value)
		q = q[:-2] + ')'

		return q, values

	def _update(self):
		values = []
		q = 'UPDATE %s SET ' % self.__stor_name__

		for name, value in self.__changes__.iteritems():
#			if isinstance(value, ReferenceList):
#				continue

			q += "%s = ?, " % name

#			if isinstance(self.__fields__[name], Reference):
#				value = getattr(value, value.__pk__[0].name)
			values.append(self.__fields__[name].serialize(value))
		q = q[:-2] + ' WHERE '

		for pk in self.__pk__:
			q += "%s = ? AND " % pk.name
			values.append(self.__origin__[pk.name])
			self.__origin__[pk.name] = getattr(self, pk.name)

		q = q[:-4]
		return q, values

	@classmethod
	def get(cls, lazy=True, **kwargs):
		values = []
		q      = "SELECT * FROM %s WHERE " % cls.__stor_name__

		for k, v in kwargs.iteritems():
			q += "%s = ? AND " % k
			values.append(v)

		q = q[:-4]

		res = []
		for item in Storage.__instance__.query(q, values):
			obj = object.__new__(cls)
			obj.__init__()

			for name, fld in obj.__fields__.iteritems():
				if isinstance(fld, ReferenceSet):
					continue

				if isinstance(fld, Reference):
					obj.__dict__[name] = Ghost(fld.__owner__, {name: item[name]})
				else:
					obj.__dict__[name] = item[name]
				if fld.pk:
					obj.__origin__[name] = item[name]

			obj.__dict__['__saved__'] = True
			obj.__changes__.clear()
			obj.__dict__['__changed__'] = False

			res.append(obj)

		return res

