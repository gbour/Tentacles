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
from tentacles.values import o2m_RefList, m2m_RefList

class FakeObject(object):
	def __init__(self, name):
		self.name        = name
		self.__changed__ = False

	def __setattr__(self, name, value):
		self.__dict__[name] = value
		self.__dict__['__changed__'] = True

	def save(self):
		pass

	def __repr__(self):
		return "FakeObject(%s)" % self.name
	__str__ = __repr__

class Test_o2mReflist(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		unittest.TestCase.__init__(self, *args, **kwargs)

		self.l = o2m_RefList()
		# owner is the object owning RefList instance
		self.o            = FakeObject('owner')
		self.l.__owner__  = self.o
		# target is the remote (Object type, fieldname)
		# remember we are in a one2many relation
		#			FakeObject(owner):  -> many -> FakeObject(target)
		#		                      <- one  <-   rtarget field
		self.l.__target__ = (FakeObject, 'rtarget')

	def test01_init(self):
		self.assertEqual(len(self.l.__items__), 0)
		self.assertEqual(len(self.l.__added__), 0)
		self.assertEqual(len(self.l.__removed__), 0)
		self.assertFalse(self.l.has_changed())

	def test02_add(self):
		t = FakeObject('target1')
		self.assertFalse(hasattr(t, 'rtarget'))

		self.l.append(t)

		self.assertEqual(len(self.l.__items__), 1)
		self.assertEqual(len(self.l.__added__), 1)
		self.assertEqual(len(self.l.__removed__), 0)
		self.assertTrue(self.l.has_changed())

		# test value propagation
		self.assertEqual(t.rtarget, self.o)

		# trying to add twice the same object
		self.l.append(t)
		self.assertEqual(len(self.l.__items__), 1)
		self.assertEqual(len(self.l.__added__), 1)
		self.assertEqual(len(self.l.__removed__), 0)
		self.assertTrue(self.l.has_changed())
		self.assertEqual(t.rtarget, self.o)

	def test02_remove(self):
		t = FakeObject('target1')
		self.l.append(t)

		self.assertEqual(len(self.l.__items__), 1)
		self.assertEqual(len(self.l.__added__), 1)
		self.assertEqual(len(self.l.__removed__), 0)
		self.assertTrue(self.l.has_changed())

		self.l.remove(t)
		self.assertEqual(len(self.l.__items__), 0)
		self.assertEqual(len(self.l.__added__), 0)
		self.assertEqual(len(self.l.__removed__), 0)
		self.assertFalse(self.l.has_changed())

		self.assertRaises(ValueError, self.l.remove, t)

		# del()
		self.l.append(t)

		self.assertTrue(self.l.has_changed())
		self.assertRaises(IndexError, operator.__delitem__, self.l, 10)

		del self.l[0]
		self.assertEqual(len(self.l.__items__), 0)
		self.assertEqual(len(self.l.__added__), 0)
		self.assertEqual(len(self.l.__removed__), 0)
		self.assertFalse(self.l.has_changed())

		self.assertRaises(IndexError, operator.__delitem__, self.l, 0)

	def test03_clear(self):
		self.l.append(FakeObject('t1'))
		self.l.append(FakeObject('t2'))
		self.assertEqual(len(self.l.__items__), 2)
		self.assertEqual(len(self.l.__added__), 2)
		self.assertEqual(len(self.l.__removed__), 0)
		self.assertTrue(self.l.has_changed())

		self.l.clear()
		self.assertEqual(len(self.l.__items__), 0)
		self.assertEqual(len(self.l.__added__), 0)
		self.assertEqual(len(self.l.__removed__), 0)
		self.assertFalse(self.l.has_changed())

	def test04_save(self):
		t1 = FakeObject('t1')
		t2 = FakeObject('t2')
		self.l.append(t1)
		self.l.append(t2)
		self.assertEqual(len(self.l.__added__), 2)
		self.assertTrue(self.l.has_changed())

		self.l.save()
		self.assertEqual(len(self.l.__items__), 2)
		self.assertEqual(len(self.l.__added__), 0)
		self.assertEqual(len(self.l.__removed__), 0)
		self.assertFalse(self.l.has_changed())

		self.l.append(FakeObject('t3'))		
		self.assertEqual(len(self.l.__items__), 3)
		self.assertEqual(len(self.l.__added__), 1)
		self.assertEqual(len(self.l.__removed__), 0)
		self.assertTrue(self.l.has_changed())

		self.l.save()
		self.assertEqual(len(self.l.__items__), 3)
		self.assertEqual(len(self.l.__added__), 0)
		self.assertEqual(len(self.l.__removed__), 0)
		self.assertFalse(self.l.has_changed())

		self.l.remove(t2)
		self.assertEqual(len(self.l.__items__), 2)
		self.assertEqual(len(self.l.__added__), 0)
		self.assertEqual(len(self.l.__removed__), 1)
		self.assertTrue(self.l.has_changed())

		self.l.save()
		self.assertEqual(len(self.l.__items__), 2)
		self.assertEqual(len(self.l.__added__), 0)
		self.assertEqual(len(self.l.__removed__), 0)
		self.assertFalse(self.l.has_changed())


class Test_m2mReflist(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		unittest.TestCase.__init__(self, *args, **kwargs)

		self.l = m2m_RefList()
		self.o = FakeObject('owner')

		self.l.__owner__  = self.o
		self.l.__target__ = (FakeObject, 'peer') 
		self.o.l          = self.l

		self.o.peer       = m2m_RefList('remote')
		self.o.peer.__owner__ = self.o
		

	def test01_init(self):
		self.assertEqual(len(self.l.__items__), 0)
		self.assertEqual(len(self.l.__added__), 0)
		self.assertEqual(len(self.l.__removed__), 0)
		self.assertFalse(self.l.has_changed())

	def test02_add(self):		
		r1 = FakeObject('r1')
		r1.peer           = m2m_RefList('remote')
		r1.peer.__owner__ = r1

		self.l.append(r1)
		self.assertEqual(len(self.l.__items__), 1)
		self.assertEqual(len(self.l.__added__), 1)
		self.assertEqual(len(self.l.__removed__), 0)
		self.assertTrue(self.l.has_changed())
		self.assertEqual(self.l[0], r1)

		# test peer
		self.assertEqual(len(r1.peer.__items__), 1)
		self.assertEqual(len(r1.peer.__added__), 1)
		self.assertEqual(len(r1.peer.__removed__), 0)
		self.assertTrue(r1.peer.has_changed())
		self.assertEqual(r1.peer[0], self.o)

	def test03_remove(self):
		r1 = FakeObject('r1')
		r1.peer           = m2m_RefList('remote')
		r1.peer.__owner__ = r1
		self.l.append(r1)
	
		self.l.remove(r1)
		self.assertEqual(len(self.l.__items__), 0)
		self.assertEqual(len(self.l.__added__), 0)
		self.assertEqual(len(self.l.__removed__), 0)
		self.assertFalse(self.l.has_changed())

		self.assertEqual(len(r1.peer.__items__), 0)
		self.assertEqual(len(r1.peer.__added__), 0)

		# remove twice: fail
		self.assertRaises(ValueError, self.l.remove, r1)

		self.l.append(r1)
		# remove by position
		del self.l[0]
	
		# remove twice: fail
		self.assertRaises(IndexError, operator.__delitem__, self.l, 0)

	def test04_removeremote(self):
		# remove from remote object
		r1 = FakeObject('r1')
		r1.peer            = m2m_RefList('remote')
		r1.peer.__owner__  = r1
		r1.peer.__target__ = (FakeObject, 'l')
		self.l.append(r1)
	
		r1.peer.remove(self.o)
		self.assertEqual(len(self.l.__items__), 0)
		self.assertEqual(len(self.l.__added__), 0)
		self.assertEqual(len(self.l.__removed__), 0)
		self.assertFalse(self.l.has_changed())

		self.assertEqual(len(r1.peer.__items__), 0)
		self.assertEqual(len(r1.peer.__added__), 0)

	def test05_clear(self):
		#TODO
		pass

	def test06_save(self):
		#TODO
		pass

	def test07_ghost(self):
		#TODO. test Ghost()
		pass


if __name__ == '__main__':
	unittest.main()
