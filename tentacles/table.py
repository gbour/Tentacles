# -*- coding: utf8 -*-
"""
    tentacles, python ORM
    Copyright (C) 2010-2011, Guillaume Bour <guillaume@bour.cc>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 3.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
__author__  = "Guillaume Bour <guillaume@bour.cc>"
__version__ = "$Revision$"
__date__    = "$Date$"

import sys, types, inspect, weakref
from odict import odict

from tentacles          import Storage
from tentacles          import fields as fieldsmod
from tentacles.lazy     import Ghost
from tentacles.fields   import Field, Reference, ReferenceSet
from tentacles.values   import RefList, m2m_RefList
from tentacles.queryset import ReduceQuerySet


#TODO: MetaObject should inherit from BaseQuerySet. Must check possible side effects?
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
		dct['__cache__']  = weakref.WeakValueDictionary()

		klass = type.__new__(cls, name, bases, dct)

		for fld in fields.itervalues():
			fld.__owner__ = klass

			if isinstance(fld, Reference) and not fld.__auto__:
				# create sibling reference
				siblname = fld.remote[1]
				if not siblname:
					siblname   = "%s__%s" % (name, fld.name)
					fld.remote = (fld.remote[0], siblname)

				ref = ReferenceSet(klass, name=fld.name, sibling=fld, reverse=True)
				ref.name      = siblname
				ref.__owner__ = fld.remote[0]
#				ref.__inherit__(Storage.__instance__)
				Storage.inherit(ref)

				fld.remote[0].__fields__[siblname] = ref
				fld.remote[0].__refs__.append(ref)

				fld.sibling = ref
				
				klass.__refs__.append(fld)
			elif isinstance(fld, ReferenceSet):
				klass.__refs__.append(fld)

		if not klass.__name__ == 'Object':
			Storage.register(klass)

		fieldsmod.ORDER += 10
		
		return klass

#	def __iter__(self):
#		from tentacles import QuerySet
#		return QuerySet(self).__iter__()
		
	def __getitem__(self, key):
		from queryset import SliceQuerySet
		#return QuerySet(self).__getitem__(key)
		return SliceQuerySet(self, key)

	### QuerySet operations ###
	#TODO: any side effects ?
	def __len__(self):
		"""
			NOTE: MUST return an integer (or python raise TypeError exception)
		"""
		return ReduceQuerySet(self, 'len').get()


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
	# instances currently in memory : created in metaobject
	#__cache__       = weakref.WeakValueDictionary()


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

#			if inspect.isfunction(obj):                                 # static method
#					obj = types.MethodType(obj, None)
			if isinstance(obj, types.MethodType):
				if obj.im_self is not None:                               # class method
					obj = types.MethodType(obj.im_func, cls)
				else:
					obj = obj.im_func
			
			setattr(cls, name, obj)
			
		for fld in cls.__fields__.itervalues():
#				print "fld=", fld
				fld.__inherit__(database)

	def __init__(self, *args, **kw):
		"""Create a new instance of *Object*

			* Each positional argument must match declared fields (in the same order).
			* Positional argument has priority over named argument.
			* All non-valued fields will be set with default field value.
		"""
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
		# check field value
		if not key in self.__fields__:
			# not a managed field
			self.__dict__[key] = value; return
			#raise Exception('Unknown field %s' % key)

		#TODO: does not set if values are same
		if self.__values__[key] == value:
			return False

#		if not key in self.__origin__:
#			self.__origin__[key] = getattr(self, key)

		fld = self.__fields__[key]
		# raise exception if failed
		if not fld.check(value):
			raise TypeError("%s.%s type is %s" % (self.__class__.__name__, key,	self.__fields__[key]))

		# normally, ReferenceSet field are set for once at all
		if propchange:
			if isinstance(fld, ReferenceSet):
					#TODO: must write it in a different way;
					# ReferenceSet field must have been previously initialized
					# then we just clear and fill field with our values
					# (checking value is iterable and items are of the correct type)
					if not isinstance(value, RefList):
						newvalue = self.__fields__[key].default()
						newvalue.__owner__  = self
						newvalue.__name__   = key
						newvalue.__target__ = fld.remote # tuple Object, fieldname						
						
						for item in value:
							newvalue.append(item)
						value = newvalue
					else:
						value.__owner__  = self
						value.__name__   = key
						value.__target__ = fld.remote # tuple Object, fieldname

		# setting a Reference value => must update sibling ReferenceSet
			elif isinstance(fld, Reference):
				# update oldref
				oldref = getattr(self, key)
				if oldref:
					refset = getattr(oldref, fld.remote[1])
					# if we delete from peer, self is no more in refset
					if self in refset:
						refset.__remove__(self)
				
				# we can set None as new value
				if value is not None:
					refset = getattr(value, fld.remote[1])
					refset.__append__(self)

				self.__changes__[key] = value

				if key not in self.__origin__:
					self.__origin__[key] = getattr(self, key)
			else:
				self.__changes__[key] = value

		self.__values__[key]         = value

		if propchange:
			self.__dict__['__changed__'] = True

		return True

	def __reset__(self):
		"""Reset changes
		"""

		self.__changes__.clear()
		self.__dict__['__changed__'] = False
	
	def __getattr__(self, name):
		"""Apply only to attributes no found in object __dict__
		"""
		value = self.__values__[name]

		if isinstance(value, Ghost):
			print 'value=', value
			dbres = value.load()
			print 'dbres=',dbres
			if len(dbres) == 0:
				#TODO: see what is the impact
				#      particularly, ReferenceSet field may return empty
				#      list, not None

				#raise Exception("NotFound")
				return None
			value = dbres[0]
			self.__setattr__(name, value, propchange=False)

			#TODO: update peer ReferenceSet when Reference
		return value

	def has_changed(self):
		"""Return **True** if *Object* instance has been modified since last save, **False** otherwise"""
		return self.__changed__

	def changes(self):
		"""Return list of changed fields since last save, in a dictionary where key is
		field name and value the new value to-be-saved
		"""
		return self.__changes__

	def saved(self):
		"""Return **True** if *Object* is saved in storage, **False** else"""
		return self.__saved__

	def __repr__(self):
		return '%s(%s=%s)' % \
			(self.__class__.__name__, self.__pk__[0].name, getattr(self, self.__pk__[0].name))

	def fieldesc(self, name):
		"""Return Field descriptor matching name

		Raise a **KeyError** exception if not found.
		"""
		return self.__fields__[name]
