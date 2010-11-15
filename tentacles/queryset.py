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

import sys, inspect, types
from reblok import Parser, opcodes

from tentacles import *
from tentacles.fields import ReferenceSet, Reference
from tentacles.inheritance import Inherit

from tentacles import py2sql, sqlcodes
from tentacles import Storage as Stor
from tentacles.lazy     import Ghost

class BaseQuerySet(Inherit):
	def __init__(self, target):
		if not isinstance(target, BaseQuerySet):
			target = RootQuerySet(target)
		self.target     = target

	def _target(self):
		return self.target._target()

	def __iter__(self):
		Qtree = self._resolve()

		# return raw result: list of values
		Q, values, fmt = self.ast2query(Qtree)
		rset = Stor.__instance__.query(Q, values)

		target = self._target()
		
		def __iterator__():
			i = 0
			l = len(rset)

			while i < l:
				yield self._initobj(rset[i], target, fmt)
				i += 1

			raise StopIteration
		
		return __iterator__()

	def _resolve(self):
		return self.target._resolve()

	def _initobj(self, rset, target, fmt):
		"""Transform a list of values into an object
		"""
		# return cached value if exist
		if rset[target.__pk__[0].name] in target.__cache__:
			return target.__cache__[rset[target.__pk__[0].name]]

		obj = object.__new__(target)
		obj.__init__()

		for name, fld in obj.__fields__.iteritems():
			if isinstance(fld, ReferenceSet):
				value = Ghost(obj, fld, fld.remote[0], {fld.remote[0].__pk__[0].name: fld.default()})
			else:
				value = fld.sql2py(rset[name])
				if isinstance(fld, Reference):
					if value in fld.remote[0].__cache__:
						value = fld.remote[0].__cache__[value]
					else:
						value = Ghost(obj, fld, fld.remote[0], {fld.remote[0].__pk__[0].name: value})
					
			obj.__setattr__(name, value, propchange=False)
			if fld.pk:
				obj.__origin__[name] = rset[name]

		obj.__dict__['__saved__'] = True
		obj.__changes__.clear()
		obj.__dict__['__changed__'] = False
		obj.__reset__()

		target.__cache__[getattr(obj, target.__pk__[0].name)] = obj
		return obj

	def __getitem__(self, key):
		"""
			Either used to get one value (key is integer) or slice (key is slice)
		"""
		if isinstance(key, slice):
			_slice = key
		elif isinstance(key, int): # int
			_slice = slice(key, None, None)
		else:
			raise(Exception(""))
			
		return SliceQuerySet(self, _slice)

	def __rshift__(self, arg):
		if not hasattr(arg, '__iter__'):
			arg = (arg,)
		return OrderQuerySet(self, +1, arg)

	def __lshift__(self, arg):
		if not hasattr(arg, '__iter__'):
			arg = (arg,)
		return OrderQuerySet(self, -1, arg)

	def __xlen__(self):
		"""
			NOTE: MUST return an integer (or python raise TypeError exception)
		"""
		return ReduceQuerySet(self, 'len').get()

class RootQuerySet(BaseQuerySet):
	def __init__(self, target):
		self.target = target

	def _target(self):
		return self.target

	def _resolve(self):
		"""
			Query AST
				1. action
				2. fields
				3. datasource
				4. condition
				5. result order
				6. limit
		"""
		return [sqlcodes.SELECT, None, self.target, None, [], None]
		
class OrderQuerySet(BaseQuerySet):
	def __init__(self, target, order, fields):
		super(OrderQuerySet, self).__init__(target)

		self.order  = order  # +1 or -1
		self.fields = fields

	def _resolve(self):
		target = self.target._resolve()
		for fld in self.fields:
			target[4].append((fld, self.order))

		return target

class SliceQuerySet(BaseQuerySet):
	def __init__(self, target, slice):
		super(SliceQuerySet, self).__init__(target)

		self.slice = slice

	def _resolve(self):
		target    = self.target._resolve()
		if target[5] is None:
			target[5] = self.slice
		else:
			target = [sqlcodes.SELECT, None, target, None, [], self.slice]

		return target

class FilterQuerySet(BaseQuerySet):
	def __init__(self, target, conditions=None):
		"""
			target   : Queryset target.
				may be either a MetaObject (Object definition) or another sub-queryset

			condition: queryset condition. It is a python AST as returned by reblok
				it may be:
					1. a lambda expression
					2. a function call      (in the future)

				If it's a lambda expression, we simplify by only keeping the conditional part
				i.e
					lambda u: u.name == 'john'

					['function', '<lambda>', [['ret', ('eq', ('attr', ('var', 'u', 'local'),
					'name'), ('const', 'john'))]], [('u', '<undef>')], None, None, [], None]

					(('eq', ('attr', ('var', 'u', 'local'), 'name'), ('const', 'john')), [('u',
					'<undef>')], [])

					we have: 1) the expression, 2) the argument, 3) the global variables used
		"""
		super(FilterQuerySet, self).__init__(target)

		self.conditions = Parser().walk(conditions)
		print self.conditions

		# for now, we only allow lambda expressions
		assert(self.conditions[0] == sqlcodes.FUNC and self.conditions[1] == '<lambda>')
		self.conditions = (
				self.conditions[2][0][1], # expression
				self.conditions[3],
				self.conditions[6],
				self.conditions[7]
				)

	def _resolve(self):
		target = self.target._resolve()

		if isinstance(self.target, SliceQuerySet):
			target = [sqlcodes.SELECT, None, target, self.conditions, [], None]
		elif isinstance(self.target, FilterQuerySet):
			#TODO: a bit more complex (merge expression, args renames, global vars)
			target[3] = (sqlcodes.AND, target[3], self.conditions)
		else:
			target[3]  = self.conditions

		return target

class ReduceQuerySet(BaseQuerySet):
	def __init__(self, target, op):
		super(ReduceQuerySet, self).__init__(target)

		self.op = op

	def get(self):
		Qtree = self._resolve()

		Q, values, fmt = self.ast2query(Qtree)
		rset = Stor.__instance__.query(Q, values)

		return rset[0][0]

	def _resolve(self):
		"""
			MUST return a unique value
		"""
		target = self.target._resolve()
		target[1] = 'len'
		
		return target

class MapQuerySet(BaseQuerySet):
	def __init__(self, target, fields):
		"""
			fields is a lambda expression, returning either:
				a single field
				a list
				a dict

			each individual field can be an expression
		"""
		super(MapQuerySet, self).__init__(target)

		self.fields = Parser().walk(fields)

	def _resolve(self):
		target = self.target._resolve()
		target[1] = self.fields

		return target

	def _initobj(self, rset, target, fmt):
		"""Transform a list of values into an object
		"""
		if fmt == 'single':
			rset = rset[0]
		elif fmt == 'dict':
			rset = dict(rset)

		return rset

orig_filter = filter
def filter(fnc, target):
	from tentacles.table import MetaObject
	if isinstance(target, BaseQuerySet) or isinstance(target, MetaObject):
		return FilterQuerySet(target, fnc)

	return orig_filter(fnc, target)

orig_map = map
def map(fnc, target):
	from tentacles.table import MetaObject
	if isinstance(target, BaseQuerySet) or isinstance(target, MetaObject):
		return MapQuerySet(target, fnc)

	return orig_map(fnc, target)

orig_len = len
def len(obj):
	from tentacles.table import MetaObject
	if isinstance(obj, BaseQuerySet) or isinstance(obj, MetaObject):
		return obj.__xlen__()

	return orig_len(obj)

#def reduce():
#	pass
#


#class Function(Opcode):
#	def __init__(self, name, args):
#		self.name   = name
#		self.args   = args
#		self.kwargs = {}
#
#	def setAttribute(self, attr):
#		self.attrs.append(attr)
#		
#	def addKWArg(self, key, value):
#		self.kwargs[key] = value
#		
#	def __str__(self):
#		s = "%s(" % self.name
#		for arg in self.args:
#			s += str(arg) + ","
#		for k, v in self.kwargs.iteritems():
#			s += "%s=%s," % (k, v)
#		s += ")"
#		return s

