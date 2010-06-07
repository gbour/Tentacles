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
from tentacles import *
import byteplay as byte

class MetaQuerySet(type):
	def __new__(cls, name, bases, dct):
		klass = type.__new__(cls, name, bases, dct)
		Storage.inherit(klass)

		return klass

class QuerySet(object):
	__metaclass__ = MetaQuerySet

	@classmethod
	def __inherit__(cls, database):
		"""Inherit attributes and methods from database backend
		"""
		modname = "tentacles.backends.%s" % database.uri.scheme
		exec "import %s" % modname
		backend = getattr(sys.modules[modname], 'QuerySet')
		print backend

		for name, obj in inspect.getmembers(backend):
			if name.startswith('__') or hasattr(cls, name):
				continue

			if isinstance(obj, types.MethodType):
				if obj.im_self is not None:                               # class method
					obj = types.MethodType(obj.im_func, cls)
				else:
					obj = obj.im_func
			
			setattr(cls, name, obj)

	def __init__(self, obj=None, flit=None):
		"""
			obj  = object
			flit = filter
		"""
		self.obj   = obj
		self.flit  = flit
		self.slice = None
		
	def setflit(self, flit):
		self.flit = flit

	def __getitem__(self, key):
		"""
			Either used to get one value (key is integer) or slice (key is slice)
		"""
		print "getitem", key, type(key)
		if isinstance(key, slice):
			self.slice = key
		else: # str
			self.slice = [key, key+1]
			
		return self
		
	def __iter__(self):
		print "GET UTER"

def filter(lep, qset):
	print qset, issubclass(qset, Object)
	if issubclass(qset, Object):
		qset = QuerySet(qset)
	qset.setflit(lep)
	
	return qset


def map():
	pass
	
def reduce():
	pass

def list(iterator):
	print "get list from", iterator

""" Instrutions """
class Op(object):
	""" Operations (booleans, numeric)
	"""
	def __new__(cls, *args, **kwargs):
#		print 'op new', cls, args, kwargs
		
		klass = None
		if args[0] == '==' or args[0] == 'is' :
			klass = EqOp
		if args[0] == '!=' or args[0] == 'is not' :
			klass = NeqOp
		if args[0] == 'not':
			klass = NotOp
		if args[0] == 'in':
			klass = InOp
		if args[0] == 'not in':
			klass = NotinOp

		elif args[0] == 'or':
			klass = OrOp
		elif args[0] == 'and':
			klass = AndOp
		elif args[0] == '+':
			klass = AddOp
			
#		print 'klass=', klass
		return object.__new__(klass, *args, **kwargs)

class UnaryOp(Op):
	""" An unary operation as only one operand
	"""
	def __init__(self, op, stack):
		self.operand = stack.pop()

	def __str__(self):
		return "%s %s " % (self.op, self.left)

class NotOp(UnaryOp):
	op = 'not'
	
class BinaryOp(Op):
	""" A binary operation as 2 operands (left and right)
	"""
	def __init__(self, op, stack):
		self.right = stack.pop()
		self.left  = stack.pop()

	def __str__(self):
		return "%s %s %s " % (self.left, self.op, self.right)

#	def sql(self, *args):
#		return "%s %s %s " % (self.left.sql(*args), self.sqlop, self.right.sql(*args))

class EqOp(BinaryOp):
	""" equal comparison """
	op = '=='

class InOp(BinaryOp):
	""" in comparison (set of values) """
	op = 'in'

class BoolOp(Op):
	"""
	"""
	def __init__(self, op, label=None, stack=None):
		self.label = label

	def __str__(self):
		return "(%s %s %s)" % (self.left, self.op, self.right)

class OrOp(BoolOp):
	op = 'or'

class AndOp(BoolOp):
	op = 'and'

class AddOp(BinaryOp):
	op = '+'


class Variable(object):
	def __init__(self, name):
		self.name = name
		self.attrs = []

	def setAttribute(self, attr):
		self.attrs.append(attr)

	def __str__(self):
		s = str(self.name)
		if len(self.attrs) > 0 :
			s += '.' + '.'.join(self.attrs)

		return s


class Value(object):
	def __new__(cls, *args, **kwargs):
		klass = None
		if isinstance(args[0], str):
			klass = StrValue
		elif isinstance(args[0], int):
			klass = IntValue
		elif isinstance(args[0], list) or isinstance(args[0], tuple):
			klass = ListValue
			
		return object.__new__(klass, *args, **kwargs)
	
	def __init__(self, val):
		self.val = val


class StrValue(Value):
	def __str__(self):
		return "'%s'" % self.val

class IntValue(Value):
	def __str__(self):
		return "%d" % self.val

class ListValue(Value):
	def __str__(self):
		return str(self.val)

class Function(object):
	def __init__(self, name, args):
		self.name   = name
		self.args   = args
		self.kwargs = {}

	def setAttribute(self, attr):
		self.attrs.append(attr)
		
	def addKWArg(self, key, value):
		self.kwargs[key] = value
		
	def __str__(self):
		s = "%s(" % self.name
		for arg in self.args:
			s += str(arg) + ","
		for k, v in self.kwargs.iteritems():
			s += "%s=%s," % (k, v)
		s += ")"
		return s

