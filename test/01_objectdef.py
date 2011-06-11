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
import unittest
from tentacles import *
from tentacles.fields import *

class User(Object):
	id     = Integer(pk=True, autoincrement=True)
	name   = String()
	age    = Integer(default=30)
	active = Boolean(default=True)

class Test01_objectdef(unittest.TestCase):
	def setUp(self):
		pass

	def test01_object(self):
		print User.__dict__
		self.assertTrue(len(User.__fields__) == 4)
		self.assertTrue('id' in User.__fields__)
		self.assertTrue(isinstance(User.__fields__['id'], Integer))

		# primary key
		self.assertTrue(len(User.__pk__) == 1)
		self.assertTrue(isinstance(User.__pk__[0], Integer))
		self.assertTrue(User.__pk__[0] == User.__fields__['id'])

	def test02_field(self):
		f_id = User.__fields__['id']
		self.assertEqual(f_id.autoincrement, True)
		self.assertEqual(f_id.pk, True)
		self.assertEqual(f_id.name, 'id')
		self.assertEqual(f_id.default(), None)

		f_age = User.__fields__['age']
		self.assertEqual(f_age.autoincrement, False)
		self.assertEqual(f_age.pk, False)
		self.assertEqual(f_age.name, 'age')
		self.assertEqual(f_age.default(), 30)

if __name__ == '__main__':
	unittest.main()


