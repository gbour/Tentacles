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
from tentacles.inheritance import Inherit

import byteplay as byte

class QuerySet(Inherit):
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
		print "GET UTER", self.__dict__
		
		args, byte = ByteCode.parse(self.flit)
		self.__query__(byte, args[0])
		
		return iter([])

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
class Opcode(object):
	def build(self, Object, *args, **kwargs):
		print "build(%s)" % self.__class__.__name__

class Op(Opcode):
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


class Variable(Opcode):
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


class Value(Opcode):
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

class Function(Opcode):
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

class ByteCode(object):
	@staticmethod
	def parse(func):
		c = byte.Code.from_code(func.func_code)

		# 1st function argument is the "table line"
		tblarg = c.args[0]
		stack  = []
		jumps  = {}

		for line in c.code:
			if isinstance(line[0], byte.Label): # jump destination
				for instr in jumps[line[0]]:
					instr.right = stack.pop()
					instr.left  = stack.pop()
					stack.append(instr)

			elif not byte.isopcode(line):
				continue

			# local variable 
			if   line[0] == byte.LOAD_FAST:
				stack.append(Variable(line[1]))
			# extern (global) variable
			elif line[0] == byte.LOAD_GLOBAL:
				stack.append(Variable(line[1]))
			# object attribute
			elif line[0] == byte.LOAD_ATTR:
				stack[-1].setAttribute(line[1])
			elif line[0] == byte.LOAD_CONST:
				stack.append(Value(line[1]))
			elif line[0] == byte.COMPARE_OP:
				# the comparison operator is in line[1]
				stack.append(Op(line[1], stack))
			elif line[0] == byte.UNARY_NOT:
				stack.append(NotOp('not', stack))
			elif line[0] == byte.BINARY_ADD:
				stack.append(AddOp('+', stack))

			# boolean ops
			elif line[0] == byte.JUMP_IF_TRUE:
				if not line[1] in jumps:
					jumps[line[1]] = []
				jumps[line[1]].insert(0, Op('or'))

			elif line[0] == byte.JUMP_IF_FALSE:
				if not line[1] in jumps:
					jumps[line[1]] = []
				jumps[line[1]].insert(0, Op('and'))

			# 2d param is the number of func args
			elif line[0] == byte.CALL_FUNCTION:
				""" line[1] is arguments number:
							line[1] % 8                     == positional args
							line[1] - (line[1] << 8) / 2**8 = varargs
				"""
				argc    = line[1] % 256
				varargc = (line[1] - argc) / 256

				func = Function(
					stack[-1-argc-2*varargc], 
					stack[-argc-2*varargc:len(stack)-2*varargc]
				)

				for i in xrange(varargc):
					func.addKWArg(stack[len(stack)-2-2*i], stack[len(stack)-1-2*i])

				del stack[-1-argc-2*varargc:]
				stack.append(func)

		return c.args, stack.pop()

