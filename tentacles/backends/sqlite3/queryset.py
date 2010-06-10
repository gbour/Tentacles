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

import sqlite3
from tentacles import Storage as Stor
import tentacles

class QuerySet(object):
	def __query__(self, opcode, args):
		# opcode contains conditional instructions, in the form of virtual opcodes
		# argname is the name of self.obj
		
		# return: (tables, where condition)
		tables, condition, values = opcode.buildQ(locals={args[0]: self.obj}, globals={})
		tables = tables.union([self.obj.__stor_name__])
		
		q = "SELECT "
		if self.aggregate == 'len':
			q += "count(*)"
		else:
			q+= "*"
		
		q += " FROM %s WHERE %s" % (','.join(tables), condition)
		if self.slice:
			q += " LIMIT %d OFFSET %s" % (self.slice.stop-self.slice.start, self.slice.start)
		print q, values
		return Stor.__instance__.query(q, values)


class BinaryOp(object):
	def buildQ(self, locals, globals):
		tables , left , values  = self.left.buildQ(locals, globals)
		rtables, right, rvalues = self.right.buildQ(locals, globals)
		
		tables = tables.union(rtables)
		values.extend(rvalues)
		return tables, "%s %s %s" % (left, self.sqlop, right), values
		
class EqOp(object):
	sqlop = '=='
	
class GreaterOp(object):
	sqlop = '>'

class GreaterEqOp(object):
	sqlop = '>='

class BoolOp(object):
	""" false: a boolean operation can be either binary or unary """
	def buildQ(self, locals, globals):
		tables , left , values  = self.left.buildQ(locals, globals)
		rtables, right, rvalues = self.right.buildQ(locals, globals)
		
		tables = tables.union(rtables)
		values.extend(rvalues)
		return tables, "%s %s %s" % (left, self.sqlop, right), values

class AndOp(object):
	sqlop = "AND"

class OrOp(object):
	sqlop = "OR"

class InOp(object):
	sqlop = "IN"

class Variable(object):
	def buildQ(self, locals, globals):
		if self.name not in locals:
			raise Exception("Parser::Variable= %s variable not set" % self.name)

		obj = locals[self.name]
		q   = obj.__stor_name__
		if len(self.attrs) > 0 and self.attrs[0] not in obj.__fields__:
			raise Exception("object %s has no %s attribute" % (obj, self.attrs[0]))

		if len(self.attrs) > 0:
			q += "." + self.attrs[0]

		return set([obj.__stor_name__]), q, []


class Value(object):
	def buildQ(self, locals, globals):
		return [], '?', [self.val]
		
class ListValue(object):
	def buildQ(self, locals, globals):
		print self.val
		return [], "(%s)" % ','.join(['?' for x in self.val]), self.val


class Function(object):
	def buildQ(self, locals, globals):
		print "function:: buildQ=", self.name, ':', self.args
		
		if self.name == "re.match" or True:
			# LIKE
			if len(self.args) != 2:
				raise Exception()
				
			if not isinstance(self.args[0], tentacles.queryset.StrValue):
				raise Exception()
				
			# many more complex
			like = self.args[0].val
			like = like.replace(".*", "%")
			like = like.replace(".", "_")
			print "like=", like
			
			tables , q, values  = self.args[1].buildQ(locals, globals)
			values.append(like)
			q += " LIKE ?"
		
		else:
			raise Exception()

		return tables, q, values

