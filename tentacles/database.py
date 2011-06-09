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

import sys, re, inspect, types


class URI(object):
	"""
		Parse database URI, and extract composantes as object fields
	"""
	"""Storage *URI* string

		Depends on storage type, but an uri is made of at least two parts:
			#. storage type, followed by a comma (':').
			#. storage arguments.

		I.e, using a sqlite3 database, you will set the following uri::

			sqlite:/path/to/sqlite.db
	"""
	def __init__(self, raw):
		m = re.match(r"""^(?P<scheme>\w+):
			(//
				(
					(?P<username>\w+):(?P<password>\w+)
				@)?
				(?P<host>[\w.-]+)
				(:(?P<port>\d+))?
			/)?
			(?P<db>[\w:/._-]+)$""", raw, re.U|re.L|re.X)

		if m is None:
			raise Exception("Invalid URI")

		for k, v in m.groupdict().iteritems():
			setattr(self, k, v)

		if hasattr(self, 'port') and self.port is not None:
			self.port = int(self.port)


class Storage(object):
	"""Storage object
	"""
	__instance__  = None
	__objects__   = []
	__refs__      = []
	__context__   = None
	
	__inheritables__ = []
	__inheritems__   = []

	def __init__(self, uri):
		self.uri = URI(uri)

		modname = "tentacles.backends.%s" % self.uri.scheme
		if not sys.modules.has_key(modname):
			raise Exception("Unknown '%s' database backend" % self.uri.scheme)
		
		exec "from %s import *" % modname
		if not hasattr(sys.modules[modname], 'Storage'):
			raise Exception("Unknown '%s' storage backend" % self.uri.scheme)

		backend = getattr(sys.modules[modname], 'Storage')
		for name, obj in inspect.getmembers(backend):
			if name.startswith('__') or hasattr(self, name):
				continue
				
			if isinstance(obj, types.MethodType):
				obj = types.MethodType(obj.im_func, self)
			setattr(self, name, obj)
		
		self.__class__.__instance__ = self

		# call backend init method
		types.MethodType(backend.__init__.im_func, self)(self.uri)
		
		for klass in self.__inheritables__:
			klass.__inherit__(self)
		for klass in self.__inheritems__:
			klass.__metaclass__.__inherit__(klass, self)
		del self.__inheritems__[:]

	@classmethod
	def set_context(cls, name):
		@classmethod
		def _set_context(cls, obj):
			obj.__stor_name__ = '%s_%s' % (name, obj.__stor_name__)
		
		if isinstance(name, types.FunctionType):
			cls.__context__ = types.MethodType(name, cls, cls)
		else:
			cls.__context__ = _set_context

	@classmethod
	def register(cls, obj):
		"""Register objects for this storage.

			Objects register once themselves at definition time (metaclass.__init__)
		"""
		if cls.__context__:
		    cls.__context__(obj)
		cls.__objects__.append(obj)

#		if cls.__instance__:
#			obj.__inherit__(cls.__instance__)
		cls.inherit(obj)

	@classmethod
	def inherit(cls, klass):
		"""Inherit an object instance
		"""
		if cls.__instance__:
			return klass.__inherit__(cls.__instance__)
			
		cls.__inheritables__.append(klass)
	
	@classmethod
	def __inherit__(cls, klass):
		"""Inherit an object definition
		"""
		if cls.__instance__:
			return klass.__metaclass__.__inherit__(cls.__instance__)
			
		cls.__inheritems__.append(klass)

