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
from tentacles import Object
from tentacles.fields import Reference, ReferenceSet

REFORDER = 1


class SQLiteStorage(object):
	def __init__(self, uri):
		self.db = sqlite3.connect(uri.db)
		self.db.row_factory = sqlite3.Row

		self.cursor = self.db.cursor()

	def execute(self, query, args=()):
		print query, args
		try:
			res = self.cursor.execute(query, args)
		except Exception, e:
			print e, ':', query, args
		#TODO: better handling of autocommit option
		self.db.commit()

		return self.cursor.lastrowid

	def query(self, query, args=()):
		try:
			self.cursor.execute(query, args)
		except Exception, e:
			print "Query=", query, args
			print e
		return self.cursor.fetchall()

	def create(self):
		for obj in self.__objects__:
			q = obj.create()
			self.execute(q)

