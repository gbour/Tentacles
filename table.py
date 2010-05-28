# -*- coding: utf8 -*-
import sys, types, inspect
from odict import odict
from tentacles          import Storage
from tentacles.fields   import Field, Reference, ReferenceSet

from tentacles import fields as fieldsmod
from tentacles.lazy import Ghost

class MetaObject(type):
	def __new__(cls, name, bases, dct):
		fields = odict()
		pk     = []

		if not '__stor_name__' in dct:
			dct['__stor_name__'] = name.lower()
		
		for fname, fld in dct.items():
			if isinstance(fld, Field):
				fld.name = fname
				if fld.pk:
					pk.append(fld)

				fields[fname] = fld
				del dct[fname]

		fields.sort(lambda x, y: x[1].__order__ - y[1].__order__)
		pk.sort(lambda x, y: x.__order__ - y.__order__)

		dct['__fields__'] = fields
		dct['__pk__']     = pk
		dct['__refs__']   = []

		klass = type.__new__(cls, name, bases, dct)

		for fld in fields.itervalues():
#			print 'powned', fld
			fld.__owner__ = klass

			if isinstance(fld, Reference) and not fld.__auto__:
				# create sibling reference
				siblname = fld.remote[1]
				if not siblname:
					siblname   = "%s__%s" % (name, fld.name)
					fld.remote = (fld.remote[0], siblname)

				ref = ReferenceSet(klass, name=fld.name, sibling=fld, reverse=True) #fieldname=fld.name, reverse=True, peer=fld)
				ref.name      = siblname
				ref.__owner__ = fld.remote[0]
				ref.__inherit__(Storage.__instance__)

				fld.remote[0].__fields__[siblname] = ref
				fld.remote[0].__refs__.append(ref)

				fld.sibling = ref
#				fld.remote.__fields__[ref.name] = ref
#				fld.peer = ref
				
				klass.__refs__.append(fld)
#				fld.remote.__references__.append(ref)
			elif isinstance(fld, ReferenceSet):
				klass.__refs__.append(fld)

		if not klass.__name__ == 'Object':
			Storage.register(klass)

		fieldsmod.ORDER += 10
		
		return klass
	
#	def __init__(cls, name, bases, dct):
#		type.__init__(name, bases, dct)

#		if name == 'Object':
#			return

#		if cls.__table_name__ is None:
#			cls.__table_name__ = name.lower()

#		Database.register_table(cls)



class Object(object):
	__metaclass__   = MetaObject
	# stored table name
	__stor_name__        = None
	# ordered list of object fields
	__fields__      = odict()
	# list of primary key fields
	__pk__          = []
	# list of references fields
	__refs__        = []

	@classmethod
	def __inherit__(cls, database):
		"""Inherit attributes and methods from database backend
		"""
		modname = "tentacles.backends.%s" % database.uri.scheme
		exec "import %s" % modname
		backend = getattr(sys.modules[modname], 'Object')

		for name, obj in inspect.getmembers(backend):
			if name.startswith('__') or hasattr(cls, name):
				continue

#			print name, obj
#			if inspect.isfunction(obj):                                 # static method
#					obj = types.MethodType(obj, None)
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
		#   key   = fieldname (str)
		#   value = 1st old value after last save

		# fields values
		self.__dict__['__values__']  = {}
		self.__dict__['__changes__'] = {}
		self.__dict__['__saved__']   = False
		# true when a change append in the object (field value, list content)
		self.__dict__['__changed__'] = False
		# initial values
		self.__dict__['__origin__']  = {}
		# lock state
		self.__dict__['__locked__']  = False

		#
		# each single attribute is replaced either by argument value, or by 
		#   its type default value.
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
				value = fld.default(self)

			self.__values__[name] = None
			setattr(self, name, value)

			if fld.pk:
				self.__origin__[name] = value

		# object id is None until saved in backend storage
#		self.__id__		 		= None
#		self.__lock__			= False
#		self.__changes__.clear()

	def __setattr__(self, key, value, propchange=True):
		"""
			propchange: 
				. if True (default behaviour) a value change is notice in the object 
				  for future saving (value is notices in __changes__ dict)
				. if False, we don't notice this as a new value change. Used when loading
					object from database
		"""
		print 'SETATTR', key, value, type(value), propchange
		# check field value
		if not key in self.__fields__:
			raise Exception('Unknown field %s' % key)

		#TODO: does not set if values are same
#		if getattr(self, key) == value:# == self.__dict__[key]:
		if self.__values__[key] == value:
			return False

#		if not key in self.__origin__:
#			self.__origin__[key] = getattr(self, key)

		fld = self.__fields__[key]
		fld.check(value)	# raise exception if failed

		# ,normally, ReferenceSet field are set for once at all
		if propchange:
			if isinstance(fld, ReferenceSet):
					value.__owner__  = self
					value.__name__   = key
					value.__target__ = fld.remote # tuple Object, fieldname

		# setting a Reference value => must update sibling ReferenceSet
			elif isinstance(fld, Reference):
				# update oldref
				print 'is ref'
				oldref = getattr(self, key)
				if oldref:
					refset = getattr(oldref, fld.remote[1])
					print refset, type(refset)
					refset.__remove__(self)
				
				# we can set None as new value
				if value is not None:
					refset = getattr(value, fld.remote[1])
					refset.__append__(self)

				self.__changes__[key] = value

				if key not in self.__origin__:
					self.__origin__[key] = getattr(self, key)
#			if fld.reverse:
#				value.__owner__ = self

#			else:
#				self.__changes__[key] = value

#				# remove old value
#				if getattr(self, key) is not None:
#					old = getattr(self, key)
#					lst = getattr(old, fld.peer.name)
#					lst.__remove__(self)

#				# get RelationList 
#				rellist = getattr(value, fld.peer.name)
#				rellist.__append__(self)
			else:
				self.__changes__[key] = value

		self.__values__[key]         = value

		if propchange:
			self.__dict__['__changed__'] = True

	def __reset__(self):
		"""Reset changes
		"""

		self.__changes__.clear()
		self.__dict__['__changed__'] = False
		
	def __getattr__(self, name):
		"""Apply only to attributes no found in object __dict__
		"""
		value = self.__values__[name]
#		print 'GETATTR', name, value

		if isinstance(value, Ghost):
			value = value.load()[0]
			self.__setattr__(name, value, propchange=False)

			#TODO: update peer ReferenceSet when Reference

		return value

	def has_changed(self):
		return self.__changed__

	def changes(self):
		return self.__changes__

	def saved(self):
		return self.__saved__

	def __repr__(self):
		return '%s(%s=%s)' % \
			(self.__class__.__name__, self.__pk__[0].name, getattr(self, self.__pk__[0].name))
			
