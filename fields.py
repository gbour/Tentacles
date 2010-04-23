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
	def __init__(self, remote, name=None, fieldname=None, reverse=False, peer=None, **kwargs):
		"""
			remote    : remote klass
			name      : local field name
			fieldname : name of peer Reference field
			reverse   : contra-peer field
			peer      : peer Reference field
		"""
		super(Reference, self).__init__(**kwargs)

		self.remote    = remote
		self.name      = name
		self.fieldname = fieldname
		self.reverse   = reverse

		if reverse:
			self.__hidden__ = True
#			self.default    = ReferenceList()

		self.peer         = None
		if peer:
			self.peer       = peer
			self.__owner__  = peer.remote

			if self.name is None:
				self.name = "%s__%s" % (remote.__name__, peer.name)


	def __str__(self):
	    q = "%s(%s=%s)" % (self.__class__.__name__, self.name, self.__default__)
	    if self.reverse:
	        q = '*' + q
	    if self.__hidden__:
	        q = '#' + q
	    return q

	def default(self):
		return ReferenceList(self, self.fieldname) if self.reverse else None


class ReferenceSet(Field):
	def __init__(self, remote, *args, **kwargs):
		super(ReferenceSet, self).__init__(*args, **kwargs)
		
		self.remote     = remote
		self.__hidden__ = True
		
		Database.register_reference(self)



class ReferenceList(object):
	def __init__(self, field, peer):
		"""
			remote   : remote fieldname
		"""
		self.__items__    = []

		# tracking changes
		self.__added__    = []
		self.__removed__  = []

		self.__owner__    = None
		self.__fld__      = field
		self.__peer__     = peer

	def append(self, value):
		"""Update internal sets
		"""
		self.__append__(value)

		# propagate
		if value.__dict__[self.__peer__]:
			getattr(value.__dict__[self.__peer__], self.__fld__.name).remove(value)

		value.__dict__[self.__peer__] = self.__owner__

	def __append__(self, value):
		self.__items__.append(value)
		self.__added__.append(value)
		self.__owner__.__changes__[self.__fld__.name] = self

	def remove(self, value):
		self.__remove__(value)

	def __remove__(self, value):
		i = self.__items__.index(value)
		self.__delitem__(i)

	def __delitem__(self, idx):
		"""Update internal sets
		"""
		value = self.__items__[idx]
		del self.__items__[idx]
		if value in self.__added__:
			self.__added__.remove(value)
		else:
			self.__removed__.append(value)

	def __len__(self):
		return len(self.__items__)

	def save(self):
		for itm in self.__added__:
			itm.save()
		del self.__added__[:]
			
		for itm in self.__removed__:
			itm.save()
		del self.__removed__[:]

	def __unicode__(self):
		return str(self.__items__)

	def __str__(self):
		return self.__unicode__()

	def __repr__(self):
		return self.__unicode__()


