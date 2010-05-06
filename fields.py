# -*- coding: utf8 -*-

import inspect, types, sys
from tentacles import Storage
from tentacles.values import o2m_RefList, m2m_RefList

ORDER = 0

class MetaField(type):
	def __new__(cls, name, bases, dct):
		"""
			As class attributes are stored in a dictionary, python loose attributes
			definition order.

			We set __order__ attribute to each Object Field to keep this information
		"""
		global ORDER
		dct['__order__'] = ORDER
		ORDER += 1

		return type.__new__(cls, name, bases, dct)


class Field(object):
	__metaclass__ = MetaField

	@classmethod
	def __inherit__(cls, database):
		"""Inherit attributes and methods from database backend
		"""
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

	def __init__(self, name=None, allow_none=True, pk=False, **kwargs):
		"""Instanciate a new Field

			. name : field name
			. none : None value allowed
		"""
		self.__owner__   = False
		self.name        = name
		self.pk          = pk
		self.none        = allow_none
		if self.pk:
			self.none = False
		self.unique      = False
		self.__hidden__  = False

		print self, self.none
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
	    q = "%s(%s)" % (self.__class__.__name__, self.name)
	    if self.__hidden__:
	        q = '#' + q
	    return q
	    
	def __repr__(self):
	    return self.__str__()


	def default(self, *args):
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
	def __init__(self, remote, name=None, sibling=None, reverse=False, **kwargs):#, fieldname=None, reverse=False, peer=None, **kwargs):
		"""
			A Reference is a many2one relation, defined for an Object with following arguments:
				. remote (object, the ``one" part of the relation)
				. name (field name for the *remote* object - optional)

			When the Object itself (field owner) is defined (MetaClass called),
			following extra fields are setted:
				. __owner__ : field class owner
				. name      : field name


			remote    : remote klass
			name      : local field name
			fieldname : name of peer Reference field
			reverse   : contra-peer field
			peer      : peer Reference field
		"""
		super(Reference, self).__init__(**kwargs)

		self.remote    = (remote, name)
		self.sibling   = sibling
		if sibling:
			self.__hidden__ = True

		self.reverse   = reverse
		self.__auto__  = False

		self.none      = False
#		self.name      = name
		
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
#	    q = "%s(%s)" % (self.__class__.__name__, self.name)
##	    if self.reverse:
##	        q = '*' + q
##	    if self.__hidden__:
##	        q = '#' + q
#	    return q

	def default(self, *args):
		return None #ReferenceList(self, self.fieldname) if self.reverse else None


class ReferenceSet(Reference):
#	def __init__(self, remote, *args, **kwargs):
#		"""
#			A ReferenceSet is defined for an Object with following arguments:
#				. linked-to objet (called remote)

#			When the Object itself (field owner) is defined (MetaClass called),
#			following extra fields are setted:
#				. __owner__ : field class owner
#				. __name__  : field name
#		"""
#		super(ReferenceSet, self).__init__(*args, **kwargs)
#		
#		self.remote     = remote
		
#		Database.register_reference(self)

	def default(self, *args):
#		return m2m_RefList(args[0], self.name, None) #return ReferenceList(self, self.remote)
		return m2m_RefList()


