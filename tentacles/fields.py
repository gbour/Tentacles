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

import inspect, types, sys

from tentacles         import Storage
from tentacles.values  import o2m_RefList, m2m_RefList

ORDER = 10


class Field(object):
	basetype = None

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

		self.__owner__     = False
		self.name          = name
		self.pk            = pk
		self.none          = allow_none
		if self.pk:
			self.none        = False
		self.unique        = False
		self.__hidden__    = False
		self.autoincrement = False

		self.__default__     = None
		if 'default' in kwargs:
			# check if default value match basetype
			self.__default__   = kwargs['default']
			if not self.check(self.__default__):
				raise TypeError('default value must be one of', self.basetype)
		if 'unique' in kwargs:
			self.unique    = kwargs['unique']

	def check(self, value):
		if self.basetype is None or (value is None and self.none):
			return True

		# is iterable
		match = False
		if hasattr(self.basetype, '__iter__'):
			for basetype in self.basetype:
				if isinstance(value, basetype):
					match = True; break
		else:
			match = isinstance(value, self.basetype)
					
		return match

	def cast(self, value):
		raise NotImplementedError

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
	"""**Integer** field type.

	Match *int* python base type.
	"""
	#: python *Integer* field basetype
	basetype = int

	def __init__(self, name=None, allow_none=True, pk=False, autoincrement=False, *args, **kwargs):
		super(Integer, self).__init__(name, allow_none, pk, *args, **kwargs)
		"""

		* name: field name
		* allow_none: field can be None
		* pk: this field is used as *primary key* for the object
		* autoincrement: field value is autoincremented first time object is saved
		"""

		if autoincrement and not pk:
			raise Exception('only pk can be autoincremented')
		self.autoincrement = autoincrement

	def cast(self, value):
		"""Cast a python object to field basetype.

		If not compatible, raise a *ValueError* exception

		Examples:

			>>> Integer().cast(1.456)
			1
			>>> Integer().cast("42")
			42
			>>> Integer().cast(True)
			1
			>>> Integer().cast(None)
			None
			>>> Integer().cast("fail")
			ValueError('integer + fail')
		"""
		if isinstance(value, int):
			return value

		if isinstance(value, (float, bool, str, unicode)):
			return int(value)

		if value is None:
			return value
	
		raise ValueError('integer + ', value)


class String(Field):
	#: python basetypes for *String* field
	basetype = (str, unicode)

	def cast(self, value):
		"""Cast python object to *String* matching value

			NOTE: *str* values are consistently converted to *unicode*
			
			>>> String().cast('foo')
			u'foo'
			>>> String().cast(None)
			None
		"""
		if isinstance(value, (types.NoneType, unicode)):
			return value
		elif isinstance(value, str):
			return value.decode('utf-8', 'replace')

		return unicode(value, errors='replace')


class Boolean(Field):
	#: python basetype for *Boolean* field
	basetype = bool

	def cast(self, value):
		"""Cast python value/object to *Boolean* matching value

			* if value is None, returns None
			* if value is an int, returns False if value equals 0, True else
			* if value is a str/unicode, returns True if value equals '1','t','true','yes',
			False if value equals '0','f','false','no'( case doesn't matter), else raise a
			ValueError exceptions

			* all other value types raise a ValueError exception

			>>> b = Boolean()
			>>> b.cast(True)
			True
			>>> b.cast(None)
			None
			>>> b.cast(1)
			True
			>>> b.cast(42)
			True
			>>> b.cast(0)
			False
			>>> b.cast('true')
			True
			>>> b.cast('False')
			False
			>>> b.cast('foo')
			ValueError('bool foo')
		"""
		#TODO: accept none only if allowed
		if isinstance(value, (types.NoneType, bool)):
			return value
		elif isinstance(value, int):
			return bool(value)
		elif isinstance(value, (str, unicode)):
			if value.lower() in ('1', 't', 'true', 'yes'):
				return True
			elif value.lower() in ('0', 'f', 'false', 'no'):
				return False

		raise TypeError('bool ' + value)


class Binary(Field):
	#pass
	def cast(self, value):
		"""Cast python value/object to *Binary* matching value

			At the moment, all python types/objects are considered matching *Binary* field
		"""
		#TODO: temp only
		return value

	def check(self, value):
		#TODO: temp only
		return True


class Datetime(Field):
	def default(self, *args):
		"""Set default field value
		
			if default value was set to *'now'*, we return current datetime
			else we return default value
		"""
		if not hasattr(self, '__default__'):
			return None

		if self.__default__ == 'now':
			from datetime import datetime
			return datetime.now()

		return self.__default__

	def cast(self, value):
		#TODO: temp only
		return value

	def check(self, value):
		#TODO: temp only
		return True

	"""
	cast:
		int = timestamp
		str = parsing
	"""

class Reference(Field):
	def __init__(self, remote, name=None, sibling=None, reverse=False, **kwargs):
		"""
			A **Reference** is a many2one relation, defined for an *Object* with following arguments:

			* remote    : Object class, the ``one" part of the relation
			* name      : field name for the *remote* Object - optional
			* sibling   : peer Reference/ReferenceSet field (owned by remote object)
			* reverse   : *False* if this is the reference Field as set by the user,
			  *True*, if it is the automagically created sibling Reference field


			When the *Object* itself (the field owner) is defined (MetaClass called),
			following extra fields are setted:
	
			* __owner__ : field class owner
			* name      : field name

			NOTE: Do a notice about remove object field

			>>> class User(Object):
			>>>		pass
			>>>
			>>> class Group(Object):
			>>>		owner = Reference(User)
			

			>>>
			>>> g = Group(u)

			>>>	class User(Object):
			>>>		pass
			>>>
			>>> class Group(Object):
			>>>		owner = Reference(User)

			definition:
				Group.owner::Reference()         <- -> User.Group__owner::ReferenceSet()
			
			instances:
				aGroup.owner::User=aUser1				 <- -> aUser1::o2m_RefList=[
																									aGroup,
																									aGroup2,
																									...
																							 ]
			owner
				.remote    = (User, None)
				.sibling   = False
				.reverse   = False
				.__owner__ = Group
				.name      = 'owner'
		"""
		super(Reference, self).__init__(**kwargs)

		self.remote    = (remote, name)
		self.sibling   = sibling

		self.reverse   = reverse
		self.__auto__  = False

	def default(self, *args):
		return None

	def cast(self, value):
		#TODO: temp only
		return value

	def check(self, value):
		#TODO: temp only
		return True


class ReferenceSet(Reference):
	def __init__(self, *args, **kwargs):
		"""
			A ReferenceSet is defined for an Object with following arguments:
				. linked-to objet (called remote)

			It represent either a many2many relation between 2 tentacles Objects,
			or the _`many`_ part or a one2many relation

			When the Object itself (field owner) is defined (MetaClass called),
			following extra fields are setted:
				. __owner__ : field class owner
				. __name__  : field name

			ReferenceSet object is used to define relation between Objects.
			When manipulating instances, relations are materialized by (o2m|m2m)_RefLists
			
			>>> class User(Object)
			>>>		pass
			>>>
			>>> class Group(Object):
			>>>		members = ReferenceSet(User)

			definition:
				Group.members::ReferenceSet()         <- -> User.Group__members::ReferenceSet()
			
			instances:
				aGroup.members::m2m_RefList=[
																			aUser1, <- -> aUser1.Group__members::m2m_RefList=[aGroup]
																			aUser2        ...
																		]
		"""
		super(ReferenceSet, self).__init__(*args, **kwargs)

		self.__hidden__ = True

	def default(self, *args):
		"""Default ReferenceSet value is an empty RefList

			Type of RefList depends on relation between objects:
			* one2many : we get a o2m_RefList()
			* many2many: we get a m2m_RefList()
		"""
		if isinstance(self.sibling, ReferenceSet):
			val = m2m_RefList(reverse=self.reverse, sibling=self.sibling)
		else:
			val = o2m_RefList()

		return val

