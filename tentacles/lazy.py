# -*- coding: utf8 -*-
"""
    tentacle, python ORM
    Copyright (C) 2010	Guillaume Bour <guillaume@bour.cc>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

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

from tentacles.fields import ReferenceSet

class Ghost(object):
	def __init__(self, owner, field, target, pks):
		self.__owner__  = owner
		self.__field__  = field
		
		self.__target__ = target
		self.__pks__    = pks

	def load(self, cache_only=False):
		kwargs = self.__pks__.copy()
		kwargs['lazy']       = False
		kwargs['owner']      = self.__owner__
		kwargs['cache_only'] = cache_only
		
		if isinstance(self.__field__, ReferenceSet):
			print self.__field__, self.__field__.__dict__
			value = self.__field__.get(**kwargs)
		else:
			value = self.__target__.get(**kwargs)

		return value

	def __str__(self):
		return "Ghost(%s=%s)" % (self.__target__.__name__, self.__pks__)

	def __repr__(self):
		return str(self)
		
	def __eq__(self, other):
		from tentacles.table  import Object
		if isinstance(other, Object):
			return other.__class__ == self.__target__ and \
				self.__pks__.values()[0] == getattr(other, other.__pk__[0].name)
			
		return id(other) == id(self)

