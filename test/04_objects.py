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
from tentacles.table import Object, MetaObject
from tentacles import fields as f

class Test_objects(unittest.TestCase):
	def test01_rawobj(self):
		class FakeMeta(MetaObject):
			def __new__(cls, name, bases, dct):
				return type.__new__(cls, name, bases, dct)

		class User(Object):
			__metaclass__ = FakeMeta


		self.assertEqual(User.__stor_name__  , None)
		self.assertEqual(len(User.__fields__), 0)
		self.assertEqual(len(User.__pk__)    , 0)
		self.assertEqual(len(User.__refs__)  , 0)

	def test02_simpleobj(self):
		class User(Object):
			id			= f.Integer(pk=True)
			name		= f.String(default='doe')
			active	= f.Boolean(allow_none=False)
			dob			= f.Datetime()

		# default storage name
		self.assertEqual(User.__stor_name__  , 'user')
		self.assertEqual(len(User.__fields__), 4)
		self.assertEqual(len(User.__pk__)    , 1)
		self.assertEqual(len(User.__refs__)  , 0)
		self.assertTrue(isinstance(User.__pk__[0], f.Integer))
		self.assertEqual(User.__pk__[0], User.__fields__['id'])

	def test03_relationsobj(self):
		class User(Object):
			__stor_name__ = 'dauser'

			id			= f.Integer(pk=True)

		class Group(Object):
			id      = f.Integer(pk=True)
			
			owner   = f.Reference(User)
			members = f.ReferenceSet(User)

		# customize Object storage nale
		self.assertEqual(User.__stor_name__, 'dauser')

		# peer reference fields (automatically created)
		self.assertTrue('Group__owner' in User.__fields__)
		self.assertTrue('Group__members' in User.__fields__)

		# references indexes
		self.assertEqual(len(User.__refs__), 2)
		self.assertEqual(len(Group.__refs__), 2)

		print User.__dict__, Group.__dict__

"""
class User(Object):
	id      = Integer(pk=True)
	name    = String(default='John Doe')

class Group(Object):
	__stor_name__ = 'dagroup'

	id      = Integer(pk=True)
	name    = String(unique=True, none=False)

	owner   = Reference(User)
	members = ReferenceSet(User)


print '\033[91m>>\033[0m', User.__stor_name__ , User.__fields__ , User.__pk__ , User.__refs__
print '\033[91m>>\033[0m', Group.__stor_name__, Group.__fields__, Group.__pk__, Group.__refs__

print Storage.__objects__

r = Group.__fields__['owner']
print '\033[91m>>\033[0m', r.__owner__, r.name, r.remote, r.sibling
r = User.__fields__['Group__owner']
print '\033[91m>>\033[0m', r.__owner__, r.name, r.remote, r.sibling
"""

if __name__ == '__main__':
	unittest.main()
