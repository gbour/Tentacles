# -*- coding: utf8 -*-

import inspect, types, sys
from tentacles import Database

ORDER = 0

class MetaField(type):
	def __new__(cls, name, bases, dct):
		global ORDER
		dct['__order__'] = ORDER
		ORDER += 1

		return type.__new__(cls, name, bases, dct)

class Field(object):
	__metaclass__ = MetaField

	@classmethod
	def __inherit__(cls, database):
		modname = "tentacles.backends.%s.fields" % database.uri.scheme
		exec "import %s" % modname
		backend = getattr(sys.modules[modname], cls.__name__)

		for name, obj in inspect.getmembers(backend):
			if name.startswith('__') or hasattr(cls, name):
				continue

			if isinstance(obj, types.MethodType):
				if obj.im_self is not None:																# class method
					obj = types.MethodType(obj.im_func, cls)
				else:
					obj = obj.im_func
			
			setattr(cls, name, obj)

	def __init__(self, name=None, notnull=False, primary_key=False, **kwargs):
		self.name        = name
		self.notnull     = notnull
		self.pk          = primary_key
		self.unique      = False
		self.default     = None
		self.__hidden__  = False
		
		if 'default' in kwargs:
			self.default   = kwargs['default']
		if 'unique' in kwargs:
			self.unique    = kwargs['unique']
#		if 'remote' in kwargs:
#			self.remote	= kwargs['remote']
#		if 'owner' in kwargs:
#			self.owner	= kwargs['owner']

	def check(self, value):
		pass

	def __str__(self):
	    q = "%s(%s=%s)" % (self.__class__.__name__, self.name, self.default)
	    if self.__hidden__:
	        q = '#' + q
	    return q
	    
	def __repr__(self):
	    return self.__str__()


class Integer(Field):
#	type = int
	pass


class String(Field):
#	type = unicode
	pass


class Binary(Field):
	pass


class Boolean(Field):
	pass


class Datetime(Field):
	pass


class Reference(Field):
	def __init__(self, remote, reverse=False, **kwargs):
		super(Reference, self).__init__(**kwargs)

		self.remote = remote
		self.reverse = reverse
		if reverse:
			self.__hidden__ = True
		
		self.remote_field = None

	def __str__(self):
	    q = "%s(%s=%s)" % (self.__class__.__name__, self.name, self.default)
	    if self.reverse:
	        q = '*' + q
	    if self.__hidden__:
	        q = '#' + q
	    return q


class ReferenceSet(Field):
	def __init__(self, remote, *args, **kwargs):
		super(ReferenceSet, self).__init__(*args, **kwargs)
		
		self.remote     = remote
		self.__hidden__ = True
		
		Database.register_reference(self)

