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

import sys, inspect, types
from tentacles import *

class MetaInherit(type):
	def __new__(cls, name, bases, dct):
		klass = type.__new__(cls, name, bases, dct)
		Storage.__inherit__(klass)

		return klass

	@staticmethod
	def __inherit__(klass, storage):
		modname = "tentacles.backends.%s" % storage.uri.scheme
		if not sys.modules.has_key(modname):
			return False

		exec "from %s import *" % modname
		if not hasattr(sys.modules[modname], klass.__name__):
			return False

		backend = getattr(sys.modules[modname], klass.__name__)
		for name, obj in inspect.getmembers(backend):
			if hasattr(klass, name) and name not in klass.__override__:
				continue

			# instance method. we get the underlying function
			if isinstance(obj, types.MethodType):
#				obj = types.MethodType(obj.im_func, klass)
				obj = obj.im_func
			setattr(klass, name, obj)

		return True


class Inherit(object):
	__metaclass__ = MetaInherit
	__override__  = ()

