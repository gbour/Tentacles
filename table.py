
import sys, types, inspect
from odict import odict
from tentacles          import Database
from tentacles.fields   import Field, ReferenceSet
#from tentacles.fields import Field, FieldDescription, ReferenceSet

class MetaTable(type):
	def __new__(cls, name, bases, dct):
		fields = odict()
		pk     = []
		
		for oname, obj in dct.items():
			if isinstance(obj, Field):
				obj.name = oname
				if obj.pk:
					pk.append(obj)

				fields[oname] = obj
				del dct[oname]

		fields.sort(lambda x, y: x[1].__order__ - y[1].__order__)
		pk.sort(lambda x, y: x.__order__ - y.__order__)
		dct['__fields__'] = fields
		dct['__pk__']     = pk
		klass = type.__new__(cls, name, bases, dct)

		for fld in fields.itervalues():
			print fld
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
	__origin__      = {}

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
			
		for fld in cls.__fields__.itervalues():
		    fld.__inherit__(database)

	def __init__(self, *args, **kw):
		# __changes__ track changed fields 
		#		key   = fieldname
		#   value = 1st old value after last save
		self.__dict__['__changes__'] = {}
		self.__dict__['__saved__']   = False

		#
		# each single attribute is replaced either by argument value, or by 
		#		its type default value.
		# for example, the field name=String(default='john doe') is replaced 
		#   by 'john doe' string
		#
		# NOTE: we bypass the __setattr__ callback & made direct dict affectation
		args = list(args)
		for name, fld in self.__fields__.iteritems():
			value = None
			if len(args) > 0:
				value = args.pop(0)

			if name in kw:
				if value is not None:
					#TODO: emit WARNING
					pass
				value = kw[name]

			if value is None:
				value = fld.default

			self.__dict__[name] = None
			setattr(self, name, value)

			if fld.pk:
				self.__origin__[name] = value

		# object id is None until saved in backend storage
#		self.__id__		 		= None
#		self.__lock__			= False
#		self.__changes__.clear()

	def __setattr__(self, key, value):
		# check field value
		if not key in self.__fields__:
			raise Exception('Unknown field %s' % key)

		#TODO: does not set if values are same
		if getattr(self, key) == value:# == self.__dict__[key]:
			return False

#		if not key in self.__origin__:
#			self.__origin__[key] = getattr(self, key)

		fld = self.__fields__[key]
		fld.check(value)	# raise exception if failed
		self.__changes__[key] = value
		self.__dict__[key]    = value


	def has_changed(self):
		return len(self.__changes__) > 0

	def changes(self):
		return self.__changes__

	def saved(self):
		return self.__saved__
