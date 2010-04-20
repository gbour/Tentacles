
import sys, types, inspect
from tentacles          import Database
from tentacles.fields   import Field, ReferenceSet
#from tentacles.fields import Field, FieldDescription, ReferenceSet

class MetaTable(type):
	def __new__(cls, name, bases, dct):
		fields = []
		pk     = []
		
		for oname, obj in dct.items():
			if isinstance(obj, Field):
				obj.name = oname
				if obj.pk:
					pk.append(obj)

				fields.append(obj)
				del dct[oname]

		fields.sort(lambda x, y: x.__order__ - y.__order__)
		pk.sort(lambda x, y: x.__order__ - y.__order__)
		dct['__fields__'] = fields
		dct['__pk__']     = pk
		klass = type.__new__(cls, name, bases, dct)

		for fld in fields:
			fld.__owner__ = klass
		return klass
	
	def __init__(cls, name, bases, dct):
		type.__init__(name, bases, dct)

		if name == 'Table':
			return

		if cls.__table_name__ is None:
			cls.__table_name__ = name.lower()

		Database.register_table(cls)


class Table(object):
	__metaclass__   = MetaTable
	__table_name__  = None
	__pk__          = []

	@classmethod
	def __inherit__(cls, database):
		modname = "tentacles.backends.%s" % database.uri.scheme
		exec "import %s" % modname
		backend = getattr(sys.modules[modname], 'Table')

		for name, obj in inspect.getmembers(backend):
			if name.startswith('__') or hasattr(cls, name):
				continue

			if isinstance(obj, types.MethodType):
				if obj.im_self is not None:                               # class method
					obj = types.MethodType(obj.im_func, cls)
				else:
					obj = obj.im_func
			
			setattr(cls, name, obj)
			
		for fld in cls.__fields__:
		    fld.__inherit__(database)
