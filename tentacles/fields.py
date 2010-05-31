# -*- coding: utf8 -*-

import inspect, types, sys
from tentacles import Storage
from tentacles.values import o2m_RefList, m2m_RefList

ORDER = 10


class Field(object):
	def __inherit__(self, database):
		"""Inherit attributes and methods from database backend
		"""
		modname = "tentacles.backends.%s.fields" % database.uri.scheme
		exec "import %s" % modname
		backend = getattr(sys.modules[modname], self.__class__.__name__)

		for name, obj in inspect.getmembers(backend):
			if hasattr(self, name):
				continue

			if isinstance(obj, types.MethodType):
				obj = types.MethodType(obj.im_func, self)

			setattr(self, name, obj)
		self.__backend_init__()

	def __init__(self, name=None, allow_none=True, pk=False, **kwargs):
		"""Instanciate a new Field

			. name : field name
			. none : None value allowed
		"""
		global ORDER
		self.__order__ = ORDER
		ORDER += 1

		self.__owner__   = False
		self.name        = name
		self.pk          = pk
		self.none        = allow_none
		if self.pk:
			self.none = False
		self.unique      = False
		self.__hidden__  = False
		self.autoincrement = False

		if 'default' in kwargs:
			self.__default__   = kwargs['default']
		if 'unique' in kwargs:
			self.unique    = kwargs['unique']

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
		if hasattr(self, '__default__'):
			return self.__default__

		return None


class Integer(Field):
	def __init__(self, pk=False, autoincrement=False, *args, **kwargs):
		super(Integer, self).__init__(pk=pk, *args, **kwargs)

		if autoincrement and not pk:
			raise Exception('only pk can be autoincremented')
		self.autoincrement = autoincrement


class String(Field):
	pass


class Binary(Field):
	pass


class Boolean(Field):
	pass


class Datetime(Field):
	pass


class Reference(Field):
	def __init__(self, remote, name=None, sibling=None, reverse=False, **kwargs):
		"""
			A Reference is a many2one relation, defined for an Object with following arguments:
				. remote (object, the ``one" part of the relation)
				. name (field name for the *remote* object - optional)

			When the Object itself (field owner) is defined (MetaClass called),
			following extra fields are setted:
				. __owner__ : field class owner
				. name      : field name


			sibling   : peer Reference/ReferenceSet field (owned by remote object)
			reverse   : false if this is the reference Field as set by the user,
								  true, if it is the automagically created sibling Reference field

x			remote    : remote klass
x			name      : local field name
x			fieldname : name of peer Reference field
x			reverse   : contra-peer field
x			peer      : peer Reference field
		"""
		super(Reference, self).__init__(**kwargs)

		self.remote    = (remote, name)
		self.sibling   = sibling

		self.reverse   = reverse
		self.__auto__  = False

	def default(self, *args):
		return None


class ReferenceSet(Reference):
	def __init__(self, *args, **kwargs):
#		"""
#			A ReferenceSet is defined for an Object with following arguments:
#				. linked-to objet (called remote)

#			When the Object itself (field owner) is defined (MetaClass called),
#			following extra fields are setted:
#				. __owner__ : field class owner
#				. __name__  : field name
#		"""
		super(ReferenceSet, self).__init__(*args, **kwargs)

		self.__hidden__ = True

	def default(self, *args):
		if isinstance(self.sibling, ReferenceSet):
			val = m2m_RefList(reverse=self.reverse, sibling=self.sibling)
		else:
			val = o2m_RefList()

		return val
