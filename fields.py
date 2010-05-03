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
		self.__default__ = None
		self.__hidden__  = False
		
		if 'default' in kwargs:
			self.__default__   = kwargs['default']
		if 'unique' in kwargs:
			self.unique    = kwargs['unique']
#		if 'remote' in kwargs:
#			self.remote	= kwargs['remote']
#		if 'owner' in kwargs:
#			self.owner	= kwargs['owner']

	def check(self, value):
		pass

	def __str__(self):
	    q = "%s(%s=%s)" % (self.__class__.__name__, self.name, self.__default__)
	    if self.__hidden__:
	        q = '#' + q
	    return q
	    
	def __repr__(self):
	    return self.__str__()


	def default(self):
		return self.__default__


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
	def __init__(self, remote, name=None):#, fieldname=None, reverse=False, peer=None, **kwargs):
		"""
			A Reference is a many2one relation, defined for an Object with following arguments:
				. remote (object, the ``one" part of the relation)
				. name (field name for the *remote* object - optional)

			When the Object itself (field owner) is defined (MetaClass called),
			following extra fields are setted:
				. __owner__ : field class owner
				. __name__  : field name

			remote    : remote klass
			name      : local field name
			fieldname : name of peer Reference field
			reverse   : contra-peer field
			peer      : peer Reference field
		"""
		super(Reference, self).__init__(**kwargs)

		self.remote    = remote
		self.name      = name
		
#		self.fieldname = fieldname
#		self.reverse   = reverse

#		if reverse:
#			self.__hidden__ = True
##			self.default    = ReferenceList()

#		self.peer         = None
#		if peer:
#			self.peer       = peer
#			self.__owner__  = peer.remote

#			if self.name is None:
#				self.name = "%s__%s" % (remote.__name__, peer.name)


#	def __str__(self):
#	    q = "%s(%s=%s)" % (self.__class__.__name__, self.name, self.__default__)
#	    if self.reverse:
#	        q = '*' + q
#	    if self.__hidden__:
#	        q = '#' + q
#	    return q

	def default(self):
		return None #ReferenceList(self, self.fieldname) if self.reverse else None


class ReferenceSet(Field):
	def __init__(self, remote, *args, **kwargs):
		"""
			A ReferenceSet is defined for an Object with following arguments:
				. linked-to objet (called remote)

			When the Object itself (field owner) is defined (MetaClass called),
			following extra fields are setted:
				. __owner__ : field class owner
				. __name__  : field name
		"""
		super(ReferenceSet, self).__init__(*args, **kwargs)
		
		self.remote     = remote
		
		Database.register_reference(self)

	def default(self):
		return None #return ReferenceList(self, self.remote)


