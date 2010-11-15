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
from tentacles import sqlcodes, table, fields
from reblok import namespaces
from tentacles.table import MetaObject

SUBQUERY = 1
class MetaObjAttr(object):
	def __init__(self, obj, attrname):
		self.obj      = obj
		self.attrname = attrname

	def __str__(self):
		return "%s.%s" % (self.obj.__stor_name__, self.attrname)

class ObjAttr(object):
	def __init__(self, obj, attrname):
		self.obj      = obj
		self.attrname = attrname

	def __str__(self):
		return "%s.%s" % (self.obj, self.attrname)

AGGREGATIONS = {
	'len': 'COUNT(*)'
}

class BaseQuerySet(object):
	def ast2query(self, qtree):
		"""
			we need a way to associate lambda function arguments with target objects

			we also have global variables
		"""
		cc = sys._getframe()
		#print cc.f_code.co_name, cc.f_code.co_freevars

		# do we have subquery ?
		datasource = subQ = qtree[2]
		if isinstance(datasource, list):
			subQ, subvalues = self.ast2query(datasource); datasource = SUBQUERY

		Q  = 'SELECT '
		fmt = 'object'

		# selection field
		if qtree[1] is None:
			# query all field == object
			Q += "%s.*" % (self.tablesolve(datasource))
		elif isinstance(qtree[1], str):
			# aggregation
			Q += AGGREGATIONS.get(qtree[1], qtree[1])
		elif isinstance(qtree[1], list) and qtree[1][0] == 'function':
			_Q, fmt = self.mapargs(qtree[1], datasource)
			Q += _Q
		else:
			raise Exception('Unknown selection field %s' % str(qtree[1]))

		# where is the condition.
		if qtree[3] is not None:
			condition, _locals, _globals, _derefs = qtree[3]
			_globals = dict([(name, getattr(sys.modules['__main__'], name)) for name in _globals])
			# only one positional argument expected, resolved as datasource
			assert len(_locals) == 1
			_locals  = {_locals[0][0]: datasource}

			condition, tables, values = self._dispatch(condition, globals=_globals,
					locals=_locals, derefs=_derefs, target=datasource)
		else:
			tables = [datasource]
			condition = None
			values = []

		if datasource == SUBQUERY:
			Q+= ' FROM (%s)' % subQ
		else:
			Q += ' FROM ' + ','.join([self.tablesolve(table) for table in tables])
		if condition is not None:
			Q += ' WHERE %s' % condition
			# not sure we must add it anytime
			#Q += ' GROUP BY %s' % datasource.__pk__[0].name

		# ORDER
		if len(qtree[4]) > 0:
			Q += ' ORDER BY ' + ', '.join(["%s %s" % (o[0], 'ASC' if o[1] > 0 else 'DESC') for o in qtree[4]])

		# RANGE selection
		if qtree[5] is not None:
			start = qtree[5].start if qtree[5].start is not None else 0
			stop  = qtree[5].stop

			if stop is not None:
				Q += ' LIMIT %d OFFSET %d' % (stop-start+1, start)

		#print Q, values, fmt
		return Q, values, fmt

	def tablesolve(self, table):
		# relation tables are not instances of MetaObject (built dynamically)
		#if isinstance(table, MetaObject):
		if hasattr(table, '__stor_name__'):
			return table.__stor_name__

		return ast2query(table)

	def buildQ():
		pass

	OPS = {
		sqlcodes.OR  : ('BINARYOP', 'OR'),
		sqlcodes.AND : ('BINARYOP', 'AND'),

		sqlcodes.EQ  : ('COMPARISON', '='),
		sqlcodes.NEQ : ('COMPARISON', '!='),

		sqlcodes.LT  : ('BINARYOP', '<'),
		sqlcodes.GT  : ('BINARYOP', '>'),
		sqlcodes.LEQ : ('BINARYOP', '<='),
		sqlcodes.GEQ : ('BINARYOP', '>='),

		sqlcodes.IN  : ('IN', 'IN'),
		sqlcodes.NIN : ('IN', 'NOT IN'),
	}

	def _dispatch(self, instr, **kwargs):
		callback = (instr[0].upper().replace(' ', ''), None)
		if instr[0] in self.OPS:
			callback = self.OPS[instr[0]]

		kwargs['extra'] = callback[1]
		return getattr(self, 'do_%s' % callback[0])(instr, **kwargs) 

	def do_BINARYOP(self, instr, **kwargs):
		left , tables , values  = self._dispatch(instr[1], **kwargs)
		right, rtables, rvalues = self._dispatch(instr[2], **kwargs)
		
		tables = tables.union(rtables)
		values.extend(rvalues)

		#TODO: right == None values =>  "is NULL"
		return "%s %s %s" % (left, kwargs['extra'], right), tables, values


	def do_COMPARISON(self, instr, **kwargs):
		left , tables , values  = self._dispatch(instr[1], **kwargs)
		right, rtables, rvalues = self._dispatch(instr[2], **kwargs)

		tables = tables.union(rtables)
		values.extend(rvalues)

		if isinstance(left, MetaObjAttr):
			tables.add(left.obj)

			if isinstance(left.obj.__fields__[left.attrname], fields.ReferenceSet):
				assert kwargs['extra'] in ('=', '!=')

				rel = left.obj.__fields__[left.attrname]

				left = "%s.%s" % (
					left.obj.__stor_name__,
					left.obj.__pk__[0].name
				)

				if kwargs['extra'] == '!=':
					left += ' NOT'

				left += " IN (SELECT %s FROM %s AS sup WHERE %s IN (%s) GROUP BY %s HAVING COUNT(*) = %d AND COUNT(*) = (SELECT COUNT(*) FROM %s AS sub WHERE sub.%s = sup.%s))" % (
				rel.__pk_stor_names__[rel.__owner__.__pk__[0]],
				rel.__stor_name__,
				rel.__pk_stor_names__[rel.sibling.__owner__.__pk__[0]],
				','.join(['?' for v in rvalues]),
				rel.__pk_stor_names__[rel.__owner__.__pk__[0]],
				len(rvalues),
				rel.__stor_name__,
				rel.__pk_stor_names__[rel.__owner__.__pk__[0]],
				rel.__pk_stor_names__[rel.__owner__.__pk__[0]],
			)

			return left, tables, values

		if isinstance(right, MetaObjAttr):
				tables.add(right.obj)

		return "%s %s %s" % (left, kwargs['extra'], right), tables, values
			
	def do_NOT(self, instr, **kwargs):
		#print 'NOT'
		kwargs['negative'] = True
		target, tables, values = self._dispatch(instr[1], **kwargs)
		del kwargs['negative']
		return target, tables, values


	def do_IN(self, instr, **kwargs):
		left , tables , values  = self._dispatch(instr[1], **kwargs)
		right, rtables, rvalues = self._dispatch(instr[2], **kwargs)

		tables = tables.union(rtables)
		values.extend(rvalues)

		if isinstance(left, MetaObjAttr):
			tables.add(left.obj)

			if isinstance(left.obj.__fields__[left.attrname], fields.ReferenceSet):
				rel = left.obj.__fields__[left.attrname]
				# need a join
				tables.add(rel)
				
				left = "%s.%s = %s.%s AND %s.%s" % (
					left.obj.__stor_name__,
					left.obj.__pk__[0].name,
					rel.__stor_name__,
					rel.__pk_stor_names__[rel.__owner__.__pk__[0]],
					rel.__stor_name__,
					rel.__pk_stor_names__[rel.sibling.__owner__.__pk__[0]]
				)

		# target is on the left side of IN operation
		elif isinstance(left, table.MetaObject) and left == kwargs['target']:
			# TODO: here we only support one-field primary key
			tables.add(left)
			left = "%s.%s" % (left.__stor_name__, left.__pk__[0].name)

			# 1. right is also a MetaObjAttr => we do a subquery
			#TODO: optimization: transform subquery into flat join query (with DISTINCT)
			if isinstance(right, MetaObjAttr):
				rel = right.obj.__fields__[right.attrname]

				if isinstance(rel, fields.ReferenceSet):
					right = "(SELECT DISTINCT %s FROM %s)" % (
						rel.__pk_stor_names__[rel.sibling.__owner__.__pk__[0]],
						rel.__stor_name__
					)

				else: # isinstance(rel, fields.Reference):
					right = "(SELECT %s FROM %s)" % (right.attrname, right.obj.__stor_name__)

			elif isinstance(right, ObjAttr):
				rel = right.obj.__fields__[right.attrname]

				values.append(getattr(right.obj, right.obj.__pk__[0].name))
				right = "(SELECT %s FROM %s WHERE %s = ?)" % (
					rel.__pk_stor_names__[rel.sibling.__owner__.__pk__[0]],
					rel.__stor_name__,
					rel.__pk_stor_names__[rel.__owner__.__pk__[0]]
				)

		#
		# reversed IN: right part my be MetaObject, MetaObjAttr
		elif isinstance(right, MetaObjAttr):
			# we accept only object
			# later, we will accept PK raw value (integer, string, list of values)
			assert isinstance(left, table.Object)
			rel = right.obj.__fields__[right.attrname]

			tables.add(right.obj)
			values.append(getattr(left, left.__pk__[0].name))
			left = right.obj.__pk__[0].name
			right = "(SELECT %s FROM %s WHERE %s = ?)" % (
				rel.__pk_stor_names__[rel.__owner__.__pk__[0]],
				rel.__stor_name__,
				rel.__pk_stor_names__[rel.sibling.__owner__.__pk__[0]]
			)


		return "%s %s %s" % (left, kwargs['extra'], right), tables, values

	def do_ATTR(self, instr, **kwargs):
		cond, tables, values = self._dispatch(instr[1], **kwargs)
		attrname = instr[2]

		if cond == SUBQUERY:
			cond = attrname
		elif isinstance(cond, table.Object):
			assert attrname in cond.__fields__
			cond = ObjAttr(cond, attrname)
		elif isinstance(cond, table.MetaObject):
			# if attribute is a ReferenceSet, we definitively need a join
			# => reported in the caller function (IN, EQ)
			#if isinstance(cond.__fields__[attrname], fields.ReferenceSet):

			cond = MetaObjAttr(cond, attrname)
		else:
			cond = "%s.%s" % (cond, attrname)

		return cond, tables, values

	def do_AT(self, instr, **kwargs):
		"""

			instr[2] MUST be a const
		"""
		cond, tables, values = self._dispatch(instr[1], **kwargs)
		return '?', tables, [values[instr[2][1]]]

	def do_VAR(self, instr, **kwargs):
		if instr[2] == namespaces.GLOBAL:
			value = kwargs['globals'][instr[1]]
		elif instr[2] == namespaces.LOCAL:
			value = kwargs['locals'][instr[1]]
		elif instr[2] == namespaces.DEREF:
			value = kwargs['derefs'][instr[1]]
		else:
			raise Exception('unknown value %s namespace' % instr[1])

		values = []
		if isinstance(value, list) or isinstance(value, tuple):
			for item in value:
				if isinstance(item, table.Object):
					values.append(str(getattr(item, item.__pk__[0].name)))
				else:
					values.append(str(item))

			value = "(%s)" % (', '.join(['?' for x in values]))
		elif not isinstance(value, table.MetaObject) and not isinstance(value, table.Object):
			values.append(value)
			value  = '?'

		return value, set(), values

	def do_CONST(self, instr, **kwargs):
		value = instr[1]
		Q     = '?'
		if isinstance(value, bool):
			value = [1 if value else 0]
		elif isinstance(value, tuple):
			Q = "(%s)" % ','.join(['?' for v in value])
	
		else:
			value = [value]

		return Q, set(), value

	def do_LIST(self, instr, **kwargs):
		Q = []
		tables = set()
		values = []
		for subinstr in instr[1]:
			_Q, _tables, _values = self._dispatch(subinstr, **kwargs)
			Q.append(str(_Q))

		return ', '.join(Q), tables, values

	def do_CALL(self, instr, **kwargs):
		#print 'CALL', instr[1]
		"""
			NOTE: we assert instr[1] is an attribute (called function name)

			we reject unhandled methods
			left part must be an Object ReferenceSet (many2many relation)

			Currently supported methods:
				- isdisjoint      (empty sets intersection)
				- not isdisjoint  (non empty sets intersection)

		"""
		assert instr[1][0] == sqlcodes.ATTR

		fnc = instr[1][2]
		if fnc not in ('isdisjoint', 'issuperset', 'issubset'):
			raise Exception('Unhandled *%s* method' % instr[1][2])

		left , tables, values = self._dispatch(instr[1][1], **kwargs)
		right, rtables, rvalues = self._dispatch(instr[2][0], **kwargs)

		if not isinstance(left, MetaObjAttr) or\
			not isinstance(left.obj.__fields__[left.attrname], fields.ReferenceSet):
			raise Exception('')

		tables.add(left.obj)
		assert isinstance(rvalues, list)

		rel = left.obj.__fields__[left.attrname]
		# need a join

		if fnc == 'isdisjoint':
#			tables.add(rel)
#			kwargs['groupby'] =	left.obj.__pk__[0].name

			left = "%s.%s" % (
				left.obj.__stor_name__,
				left.obj.__pk__[0].name)

			if kwargs.get('negative', False) is False:
				left += ' NOT'

			left += " IN (SELECT DISTINCT %s FROM %s WHERE %s IN (%s))" % (
				rel.__pk_stor_names__[rel.__owner__.__pk__[0]],
				rel.__stor_name__,
				rel.__pk_stor_names__[rel.sibling.__owner__.__pk__[0]],
				','.join(['?' for v in rvalues]),
			)

#			left = "%s.%s = %s.%s AND %s.%s" % (
#				left.obj.__stor_name__,
#				left.obj.__pk__[0].name,
#				rel.__stor_name__,
#				rel.__pk_stor_names__[rel.__owner__.__pk__[0]],
#				rel.__stor_name__,
#				rel.__pk_stor_names__[rel.sibling.__owner__.__pk__[0]]
#			)
#
#
#			if kwargs.get('negative', False) is False:
#				left += ' NOT'
#			left += ' IN (%s)' % ','.join(['?' for v in rvalues])

		elif fnc == 'issuperset':
			left = "%s.%s IN (SELECT %s FROM %s WHERE %s IN (%s) GROUP BY %s HAVING COUNT(*) >= %d)" % (
				left.obj.__stor_name__,
				left.obj.__pk__[0].name,
				rel.__pk_stor_names__[rel.__owner__.__pk__[0]],
				rel.__stor_name__,
				rel.__pk_stor_names__[rel.sibling.__owner__.__pk__[0]],
				','.join(['?' for v in rvalues]),
				rel.__pk_stor_names__[rel.__owner__.__pk__[0]],
				len(rvalues)
			)

		elif fnc == 'issubset':
			left = "%s.%s IN (SELECT %s FROM %s AS sup WHERE %s IN (%s) GROUP BY %s HAVING COUNT(*) > 0 AND COUNT(*) <= %d AND COUNT(*) = (SELECT COUNT(*) FROM %s AS sub WHERE sub.%s = sup.%s))" % (
				left.obj.__stor_name__,
				left.obj.__pk__[0].name,
				rel.__pk_stor_names__[rel.__owner__.__pk__[0]],
				rel.__stor_name__,
				rel.__pk_stor_names__[rel.sibling.__owner__.__pk__[0]],
				','.join(['?' for v in rvalues]),
				rel.__pk_stor_names__[rel.__owner__.__pk__[0]],
				len(rvalues),
				rel.__stor_name__,
				rel.__pk_stor_names__[rel.__owner__.__pk__[0]],
				rel.__pk_stor_names__[rel.__owner__.__pk__[0]],
			)

		#print left
		return left, tables, rvalues


	"""
		map transform a resultset (object fields) into another resultset:
			- single item
			- tuple/list
			- dictionary
	"""

	def mapargs(self, expr, target):
		"""
			expr is a lambda expression, returning fields we want to retrieve
		"""
		assert len(expr[3]) == 1 # 1st and only arg is qset target
		_locals  = {expr[3][0][0]: target}
		_globals = dict([(name, getattr(sys.modules['__main__'], name)) for name in	expr[6]])

		expr = expr[2][0][1]
		Q, fmt = self.map_dispatch(expr, globals=_globals,	locals=_locals,
				target=target, action='map')

		return str(Q), fmt

	def map_dispatch(self, expr, **kwargs):
		callback, kwargs['extra'] = self.OPS.get(expr[0], (expr[0].upper().replace(' ', ''), None))

		return getattr(self, '%s_%s' % (kwargs['action'], callback))(expr, **kwargs) 

	def map_VAR(self, expr, **kwargs):
		"""

			(VAR, 'u', LOCAL)
		"""
		if expr[2] == namespaces.GLOBAL:
			val = kwargs['globals'][expr[1]]
		elif expr[2] == namespaces.LOCAL:
			val = kwargs['locals'][expr[1]]
		else:
			raise Exception('unknown value %s namespace' % expr[1])

		return val

	def map_ATTR(self, expr, **kwargs):
		"""

			(ATTR, (VAR, 'u', LOCAL), 'name')
		"""
		attrname = expr[2]
		val = self.map_dispatch(expr[1], **kwargs)
		val = "%s.%s" % (val.__stor_name__, attrname)

		return val, 'single'

	def map_LIST(self, expr, **kwargs):
		return ', '.join([self.map_dispatch(s, **kwargs)[0] for s in expr[1]]), 'list'

	def map_DICT(self, expr, **kwargs):
		Q = []
		for item in expr[1]:
			assert item[0][0] == sqlcodes.CONST
			_Q, trash = self.map_dispatch(item[1], **kwargs)
			Q.append("%s AS %s" % (str(_Q), item[0][1]))

		return ', '.join(Q), 'dict'
	

## OUTDATED ##
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

