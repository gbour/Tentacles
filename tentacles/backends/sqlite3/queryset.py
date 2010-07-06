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

import sys, sqlite3
from tentacles import Storage as Stor
import tentacles

class QuerySet(object):
	def __query__(self, opcode, args, externvars):
		# we resolve global variables
		globals = {}
		for name in externvars:
			if hasattr(sys.modules['__main__'], name):
				globals[name] = getattr(sys.modules['__main__'], name)
			else:
				globals[name] = None
#		print "GLOBALS=", globals
	
		# opcode contains conditional instructions, in the form of virtual opcodes
		# argname is the name of self.obj
		
		# return: (tables, where condition)
		
		q = "SELECT "
		if self.aggregate == 'len':
			q += "count(*)"
		else:
			q+= "*"

		if opcode:
			tables, condition, values = opcode.buildQ(locals={args[0]: self.obj}, globals=globals, operator=None)
		else:
			tables, condition, values = (set(), None, [])
		tables = tables.union([self.obj.__stor_name__])
		
		q += " FROM %s" % ','.join(tables)
		if condition:
			q += " WHERE %s" % condition
		if self.slice:
			q += " LIMIT %d OFFSET %s" % (self.slice.stop-self.slice.start, self.slice.start)
		print q, values
		return Stor.__instance__.query(q, values)


class BinaryOp(object):
	def buildQ(self, locals, globals, *args, **kwargs):
		tables , left , values  = self.left.buildQ(locals, globals, self, 'left')
		rtables, right, rvalues = self.right.buildQ(locals, globals, self, 'right')
		
		tables = tables.union(rtables)
		values.extend(rvalues)

		#TODO: right == None values =>  "is NULL"
		return tables, "%s %s %s" % (left, self.sqlop, right), values
		
class EqOp(object):
	sqlop = '='
	
class GreaterOp(object):
	sqlop = '>'

class GreaterEqOp(object):
	sqlop = '>='

class BoolOp(object):
	""" false: a boolean operation can be either binary or unary """
	def buildQ(self, locals, globals, operator):
		tables , left , values  = self.left.buildQ(locals, globals , self, 'left')
		rtables, right, rvalues = self.right.buildQ(locals, globals, self, 'right')
		
		tables = tables.union(rtables)
		values.extend(rvalues)
		return tables, "%s %s %s" % (left, self.sqlop, right), values

class AndOp(object):
	sqlop = "AND"

class OrOp(object):
	sqlop = "OR"

class InOp(object):
	sqlop = "IN"

	def buildQ(self, locals, globals, operator, *args, **kwargs):
		print "IN::buildQ"

class NotinOp(object):
	sqlop = "NOT IN"

class Variable(object):
	def buildQ(self, locals, globals, operator, pos=None):
#		print self, "OP=", operator
	
		if self.name in locals:
			val = locals[self.name]
		elif self.name in globals:
			val = globals[self.name]
		else:
			raise Exception("Parser::Variable= %s variable not set" % self.name)

		#
		if self.index is not None:
			val = val[self.index]

		from tentacles.table import Object, MetaObject
		if isinstance(val, MetaObject):
			if (isinstance(operator, tentacles.queryset.InOp) or isinstance(operator, tentacles.queryset.NotinOp)) and pos == 'right':
				field = val.__fields__[self.attrs[0]]
				print field
				
				# one2many/many2many relation 
				from tentacles.fields import ReferenceSet
				if isinstance(field, ReferenceSet):
					print "PLOP", field.__stor_name__, field.__pk_stor_names__, field.name, field.sibling
					q = "(SELECT DISTINCT %s FROM %s)" % (field.__pk_stor_names__[field.sibling.__owner__.__pk__[0]], field.__stor_name__)
					tables = []
					args   = []
					
				else:
						
					""" we must do a subquery """
					tables = []
					args   = []
					q      = "(SELECT DISTINCT %s FROM %s)" % (self.attrs[0], val.__stor_name__)
			else:
				q      = val.__stor_name__
				tables = [val.__stor_name__]
				args   = []

				if len(self.attrs) > 0:
					if self.attrs[0] not in val.__fields__:
						raise Exception("object %s has no %s attribute" % (val, self.attrs[0]))

					q += "." + self.attrs[0]

				else:
					q += "." + val.__pk__[0].name

		elif isinstance(val, Object):
			if (isinstance(operator, tentacles.queryset.InOp) or isinstance(operator, tentacles.queryset.NotinOp)) and pos == 'right':
				mylist = getattr(val, self.attrs[0])
				field  = mylist.__owner__.__fields__[mylist.__name__]
				sibling = field.sibling
				print mylist, field, field.__stor_name__, field.__pk_stor_names__, field.name, field.sibling
				q = "(SELECT %s FROM %s WHERE %s = ?)" % (field.__pk_stor_names__[sibling.__owner__.__pk__[0]], field.__stor_name__, field.__pk_stor_names__[mylist.__owner__.__pk__[0]])
				tables = []
				args   = [getattr(val, val.__pk__[0].name)]
				
			else:
				q      = '?'
				tables = []

				if len(self.attrs) > 0:
					if self.attrs[0] not in val.__fields__:
						raise Exception("object %s has no %s attribute" % (val, self.attrs[0]))

					val    = getattr(val, self.attrs[0])
					if isinstance(val, Object):
						val = val.id
					args   = [val]
				else:
					args   = [val.id] # should be dynamic
		else:
			q      = '?'
			args   = [val]
			tables = []

#		print "q=", q, self, val
		return set(tables), q, args


class Value(object):
	def buildQ(self, locals, globals, *args, **kwargs):
		return [], '?', [self.val]
		
class ListValue(object):
	def buildQ(self, locals, globals, *args, **kwargs):
		print self.val
		return [], "(%s)" % ','.join(['?' for x in self.val]), self.val


class Function(object):
	def buildQ(self, locals, globals, operator, *args, **kwargs):
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
			
			tables , q, values  = self.args[1].buildQ(locals, globals, operator)
			values.append(like)
			q += " LIKE ?"
		
		else:
			raise Exception()

		return tables, q, values

