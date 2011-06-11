# -*- coding: utf8 -*-
"""
    tentacles, python ORM
    Copyright (C) 2010-2011, Guillaume Bour <guillaume@bour.cc>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 3.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import unittest, operator
from datetime import datetime
from tentacles.database import URI

class Test_URI(unittest.TestCase):
	"""Test all sort of database URIs

		(and failing cases)
	"""
	def test01_sqlite(self):
		u = URI('sqlite3::memory:')
		self.assertEqual(u.scheme, 'sqlite3')
		self.assertEqual(u.db    , ':memory:')

		u = URI('sqlite3:/tmp/sample.db')
		self.assertEqual(u.scheme, 'sqlite3')
		self.assertEqual(u.db    , '/tmp/sample.db')

	def test02_mysql(self):
		u = URI('mysql://127.0.0.1/sampledb')
		self.assertEqual(u.scheme  , 'mysql')
		self.assertEqual(u.username, None)
		self.assertEqual(u.password, None)
		self.assertEqual(u.host    , '127.0.0.1')
		self.assertEqual(u.port    , None)
		self.assertEqual(u.db      , 'sampledb')

		u = URI('mysql://127.0.0.1:1234/sampledb')
		self.assertEqual(u.scheme  , 'mysql')
		self.assertEqual(u.username, None)
		self.assertEqual(u.password, None)
		self.assertEqual(u.host    , '127.0.0.1')
		self.assertEqual(u.port    , 1234)
		self.assertEqual(u.db      , 'sampledb')

		u = URI('mysql://foo:bar@192.168.10.27:7924/sampledb')
		self.assertEqual(u.scheme  , 'mysql')
		self.assertEqual(u.username, 'foo')
		self.assertEqual(u.password, 'bar')
		self.assertEqual(u.host    , '192.168.10.27')
		self.assertEqual(u.port    , 7924)
		self.assertEqual(u.db      , 'sampledb')

		u = URI('mysql://foo:bar@in-da.house.co.uk/my_dibi')
		self.assertEqual(u.scheme  , 'mysql')
		self.assertEqual(u.username, 'foo')
		self.assertEqual(u.password, 'bar')
		self.assertEqual(u.host    , 'in-da.house.co.uk')
		self.assertEqual(u.port    , None)
		self.assertEqual(u.db      , 'my_dibi')


if __name__ == '__main__':
	unittest.main()
