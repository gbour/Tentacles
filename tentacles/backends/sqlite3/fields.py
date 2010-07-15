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

import new
from datetime import datetime
from tentacles import Storage, Object, Ghost
from tentacles import fields

#import orm.fields as base
class Field(object):
	sql_type = ''

	def sql_protect(self, value):
		return value

	def sql2py(self, value):
		return value

	def sql_def(self):
		return "%s %s" % (self.name, self.sql_type)

	def sql_extra(self):
		return ''

	def serialize(self, value):
		return value

	def __backend_init__(self):
		"""Called at init time

			Replace lack of inheritance
		"""
		pass


class Integer(Field):
	sql_type = 'INTEGER'
	
	def __init__(self):
		print 'SQINIT'

	def sql_protect(self, value):
		return '%d' % value

class String(Field):
	sql_type = 'TEXT'
	
	def sql_protect(self, value):
		return '"%s"' % value


class Binary(Field):
	sql_type = 'BLOB'


class Boolean(Integer):
	sql_type = 'INTEGER'
	
	def sql_protect(self, value):
		return '1' if value else '0'

	def sql2py(self, value):
		return False if value == 0 else True

class Datetime(String):
	sql_type = 'TEXT'
	
	def sql_protect(self, value):
		dt = value
		
		if value == 'now':
			dt = datetime.now()
			
		return dt.strftime("\"%Y-%m-%d %H:%M:%S\"")


class Reference(Field):
	def sql_def(self):
		q = self.name
		
		if len(self.remote[0].__pk__) > 1:
			raise Exception("can't reference an Object with multi-fields primary key")
		if len(self.remote[0].__pk__) == 0:
			raise Exception("can't reference an Object without  primary key")


		#TODO: must check referenced table primary key type
		q += " INTEGER REFERENCES %s (" % self.remote[0].__stor_name__
		for pk in self.remote[0].__pk__:
		    q += "%s," % pk.name
		q = q[:-1] + ")"

		return q

	def serialize(self, value):
		if value is None:
			return None

		return getattr(value, value.__pk__[0].name)


JOIN_COUNT = 0

class ReferenceSet(Field):
#	@staticmethod
	def __backend_init__(self):
		"""We instanciate join table
		"""
		if not isinstance(self.sibling, fields.ReferenceSet) or self.reverse:
			return

		global JOIN_COUNT
		JOIN_COUNT += 1

		self.__stor_name__ = "join%03d__%s_%s" % \
			(JOIN_COUNT, self.__owner__.__stor_name__, self.name)
		self.sibling.__stor_name__ = self.__stor_name__
		
		dct = {
			'__stor_name__': self.__stor_name__,
			'__refs__': {self.__owner__: [], self.remote: []}
		}

		self.__pk_stor_names__ = {}
		for pk in self.__owner__.__pk__:
			r = fields.Reference(self.__owner__, pk=True)
			r.__auto__ = True

			self.__pk_stor_names__[pk] = "%s__%s" % (self.__owner__.__stor_name__, pk.name)
			dct["%s__%s" % (self.__owner__.__stor_name__, pk.name)] = r

		for pk in self.sibling.__owner__.__pk__:
			r = fields.Reference(self.sibling.__owner__, pk=True)
			r.__auto__ = True

			self.__pk_stor_names__[pk] = "%s__%s" % (self.sibling.__owner__.__stor_name__, pk.name)
			dct["%s__%s" % (self.sibling.__owner__.__stor_name__, pk.name)] = r


#		print '>>', self.__stor_name__, dct
		join = new.classobj(self.__stor_name__[0].upper() + self.__stor_name__[1:], 
				(Object,), dct)

	def get(self, owner=None, cache_only=False, **kwargs):
		"""Get relational datas

			2 cases:
				o2m: query remote object with local key to know which are related
				m2m: query join table to get remote object ids
		"""
		if isinstance(self.sibling, fields.ReferenceSet):
			q = "SELECT %s FROM %s WHERE %s = ?" % \
				("%s__%s" % (self.sibling.__owner__.__stor_name__, self.sibling.__owner__.__pk__[0].name),
				self.__stor_name__,
				"%s__%s" % (self.__owner__.__stor_name__, self.__owner__.__pk__[0].name))
			values = [getattr(owner, owner.__pk__[0].name)]
		else:
			q = "SELECT %s FROM %s WHERE %s = ?" % \
				(self.remote[0].__pk__[0].name, self.remote[0].__stor_name__, self.remote[1])
			values = [getattr(owner, owner.__pk__[0].name)]

		#NOTE: row is a sqlite3.Row object
		rows = Storage.__instance__.query(q, values)
		items = [Ghost(None, self.remote[1], self.remote[0], {self.remote[0].__pk__[0].name: row[0]}) for row in rows]
#		o2m_RefList
		seq = self.default()
		seq.__owner__  = owner
		seq.__name__   = self.name
		seq.__target__ = self.remote

		seq.__extend__(items)
		return [seq]

	def sql_def(self):
		raise Exception("May not happend")

	def serialize(self):
		raise Exception('May not happend')

