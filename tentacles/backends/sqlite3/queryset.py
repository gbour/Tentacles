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

class QuerySet(object):
	def __query__(self, opcode, argname):
		values = []
		q      = "SELECT * FROM %s WHERE " % self.obj.__stor_name__

		# opcode contains conditional instructions, in the form of virtual opcodes
		# argname is the name of self.obj
		opcode.build(self.obj)

		
#		for k, v in kwargs.iteritems():
#			q += "%s = ? AND " % k
#			values.append(v)

#		q = q[:-4]

#		res = []
#		for item in Storage.__instance__.query(q, values):
#			obj = object.__new__(cls)
#			obj.__init__()

#			for name, fld in obj.__fields__.iteritems():
#				if isinstance(fld, ReferenceSet):
#					value = Ghost(obj, fld, fld.remote[0], {fld.remote[0].__pk__[0].name: fld.default()})
#				else:
#					value = item[name]
#					if isinstance(fld, Reference):
#						# get from cache
#						if value in fld.remote[0].__cache__:
#							value = fld.remote[0].__cache__[value]
#						else:
#							value = Ghost(obj, fld, fld.remote[0], {fld.remote[0].__pk__[0].name: value})
#					
#				obj.__setattr__(name, value, propchange=False)
#				if fld.pk:
#					obj.__origin__[name] = item[name]

#			obj.__dict__['__saved__'] = True
#			obj.__changes__.clear()
#			obj.__dict__['__changed__'] = False
#			obj.__reset__()

#			cls.__cache__[getattr(obj, cls.__pk__[0].name)] = obj
#			res.append(obj)

#		return res
		print q


#class Variable(object):
