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

		q = q[:-2] + '\n)'
		return q

	def save(self):
		if not self.__changed__ or self.__locked__:
			return

		self.__dict__['__locked__'] = True
		# check references
		for refdef in self.__refs__:
			refval = getattr(self, refdef.name)
			if refval is not None and not refval.saved():
				refval.save()

		cache = False
		if len(self.__changes__) > 0:
			if self.__saved__:
				q, values = self._update()
			else:
				q, values = self._insert()
				self.__dict__['__saved__'] = True
				cache = True

			autoid = Storage.__instance__.execute(q, values)

			if self.__pk__[0].autoincrement:
				setattr(self, self.__pk__[0].name, autoid)

			if cache:
				self.__cache__[getattr(self, self.__pk__[0].name)] = self

		for refdef in self.__refs__:
			refval = getattr(self, refdef.name)
			if refval and refval.has_changed():
				refval.save()

			if refdef.name in self.__origin__:
				if self.__origin__[refdef.name]:
					self.__origin__[refdef.name].save()
				self.__origin__[refdef.name] = refval

		self.__changes__.clear()
		self.__dict__['__changed__'] = False
		self.__dict__['__locked__']  = False

	def _insert(self):
		values = []
		q = 'INSERT INTO %s VALUES(' % self.__stor_name__
		for name, fld in self.__fields__.iteritems():
			if isinstance(fld, ReferenceSet):
				continue

			q += '?, '
			value = getattr(self, name)
			if value is not None and isinstance(fld, Reference):
				value = getattr(value, value.__pk__[0].name)

			# check if it is ok for sqlite
			values.append(value)
		q = q[:-2] + ')'

		return q, values

	def _update(self):
		values = []
		q = 'UPDATE %s SET ' % self.__stor_name__

		for name, value in self.__changes__.iteritems():
			q += "%s = ?, " % name
			values.append(self.__fields__[name].serialize(value))

		q = q[:-2] + ' WHERE '

		for pk in self.__pk__:
			q += "%s = ? AND " % pk.name
			values.append(self.__origin__[pk.name])
			self.__origin__[pk.name] = getattr(self, pk.name)

		q = q[:-4]
		return q, values

	@classmethod
	def get(cls, lazy=True, owner=None, cache_only=False, **kwargs):
		# get from cache
		if cls.__pk__[0].name in kwargs and \
			kwargs[cls.__pk__[0].name] in cls.__cache__:
			return [cls.__cache__[kwargs[cls.__pk__[0].name]]]
	
		if cache_only:
			return None

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
					value = Ghost(obj, fld, fld.remote[0], {fld.remote[0].__pk__[0].name: fld.default()})
				else:
					value = item[name]
					if isinstance(fld, Reference):
						# get from cache
						if value in fld.remote[0].__cache__:
							value = fld.remote[0].__cache__[value]
						else:
							value = Ghost(obj, fld, fld.remote[0], {fld.remote[0].__pk__[0].name: value})
					
				obj.__setattr__(name, value, propchange=False)
				if fld.pk:
					obj.__origin__[name] = item[name]

			obj.__dict__['__saved__'] = True
			obj.__changes__.clear()
			obj.__dict__['__changed__'] = False
			obj.__reset__()

			cls.__cache__[getattr(obj, cls.__pk__[0].name)] = obj
			res.append(obj)

		return res
