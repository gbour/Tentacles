# -*- coding: utf8 -*-
import unittest, operator
from datetime import datetime
from tentacles.fields import *

class Test_fields(unittest.TestCase):
	def test01_integer(self):
		f = Integer()
		self.assertEqual(f.name         , None)
		self.assertEqual(f.none         , True)
		self.assertEqual(f.pk           , False)
		self.assertEqual(f.autoincrement, False)

		f = Integer('age')
		self.assertEqual(f.name          , 'age')

		f = Integer('age', False, True, True)
		self.assertEqual(f.name         , 'age')
		self.assertEqual(f.none         , False)
		self.assertEqual(f.pk           , True)
		self.assertEqual(f.autoincrement, True)

		f = Integer(name='age', allow_none=False, pk=True, autoincrement=True)
		self.assertEqual(f.name         , 'age')
		self.assertEqual(f.none         , False)
		self.assertEqual(f.pk           , True)
		self.assertEqual(f.autoincrement, True)
	
		# object can't be None if pk is True	
		f = Integer(allow_none=True, pk=True)
		self.assertEqual(f.none         , False)
		self.assertEqual(f.pk           , True)

		# autoincrement must be pk
		self.assertRaises(Exception, Integer, autoincrement=True)
	
		# default value	
		f = Integer(default=42)
		self.assertEqual(f.default(), 42)	

		# cast
		self.assertEqual(f.cast(42)   , 42)
		self.assertEqual(f.cast(42.57), 42)
		self.assertEqual(f.cast("42") , 42)
		self.assertEqual(f.cast(u"42"), 42)
		self.assertEqual(f.cast(True) , 1)	
		self.assertEqual(f.cast(False), 0)
		self.assertEqual(f.cast(None) , None)
		self.assertRaises(ValueError, f.cast, 'foo')

		# check
		self.assertTrue(f.check(None))
		self.assertTrue(f.check(42))
		# python consider boolean to be int
		self.assertTrue(f.check(True))
		self.assertFalse(f.check(42.7))
		self.assertFalse(f.check('42'))
		f.none = False
		self.assertFalse(f.check(None))

	def test02_string(self):
		f = String()
		self.assertEqual(f.name         , None)
		self.assertEqual(f.none         , True)
		self.assertEqual(f.pk           , False)
		self.assertEqual(f.autoincrement, False)

		f = String('age')
		self.assertEqual(f.name          , 'age')

		f = String('age', False, True)
		self.assertEqual(f.name         , 'age')
		self.assertEqual(f.none         , False)
		self.assertEqual(f.pk           , True)

		f = String(name='age', allow_none=False, pk=True)
		self.assertEqual(f.name         , 'age')
		self.assertEqual(f.none         , False)
		self.assertEqual(f.pk           , True)
	
		# object can't be None if pk is True	
		f = String(allow_none=True, pk=True)
		self.assertEqual(f.none         , False)
		self.assertEqual(f.pk           , True)
	
		# default value	
		f = String(default='foo')
		self.assertEqual(f.default(), u'foo')	

		f = String(default=u'bar')
		self.assertEqual(f.default(), u'bar')	

		# cast
		self.assertEqual(f.cast('foo') , u'foo')
		self.assertEqual(f.cast(u'bar'), u'bar')
		self.assertEqual(f.cast(None)  , None)
		self.assertRaises(TypeError, f.cast, 42)
		self.assertRaises(TypeError, f.cast, 42.7)
		self.assertRaises(TypeError, f.cast, True)

		# check
		self.assertTrue(f.check(None))
		self.assertTrue(f.check('foo'))
		self.assertTrue(f.check(u'bar'))
		self.assertFalse(f.check(42.7))
		self.assertFalse(f.check(42))
		self.assertFalse(f.check(True))
		f.none = False
		self.assertFalse(f.check(None))

	def test03_boolean(self):
		f = Boolean()
		self.assertEqual(f.name         , None)
		self.assertEqual(f.none         , True)
		self.assertEqual(f.pk           , False)
		self.assertEqual(f.autoincrement, False)

		f = Boolean('active')
		self.assertEqual(f.name         , 'active')

		f = Boolean('active', False, True)
		self.assertEqual(f.name         , 'active')
		self.assertEqual(f.none         , False)
		self.assertEqual(f.pk           , True)

		f = Boolean(name='active', allow_none=False, pk=True)
		self.assertEqual(f.name         , 'active')
		self.assertEqual(f.none         , False)
		self.assertEqual(f.pk           , True)
	
		# object can't be None if pk is True	
		f = Boolean(allow_none=True, pk=True)
		self.assertEqual(f.none         , False)
		self.assertEqual(f.pk           , True)
	
		# default value	
		f = Boolean(default=True)
		self.assertEqual(f.default(), True)	

		self.assertRaises(TypeError, Boolean, default='foo')

		# cast
		self.assertEqual(f.cast(True) , True)
		self.assertEqual(f.cast(False), False)
		self.assertEqual(f.cast(0)    , False)
		self.assertEqual(f.cast(1)    , True)
		self.assertEqual(f.cast(42)   , True)
		self.assertEqual(f.cast(-42)  , True)
	
		for v in ('1','t','T','true','True','yes','YES'):
			self.assertEqual(f.cast(v), True)
		for v in ('0','f','F','false','False','no','NO'):
			self.assertEqual(f.cast(v), False)

		self.assertRaises(TypeError, f.cast, 'foo')
		self.assertRaises(TypeError, f.cast, u'bar')
		self.assertRaises(TypeError, f.cast, 42.7)

		# check
		self.assertTrue(f.check(None))
		self.assertTrue(f.check(True))
		self.assertTrue(f.check(False))
		self.assertFalse(f.check('foo'))
		self.assertFalse(f.check(u'bar'))
		self.assertFalse(f.check(42.7))
		self.assertFalse(f.check(42))
		f.none = False
		self.assertFalse(f.check(None))

	def test04_datetime(self):
		f = Datetime()
		self.assertEqual(f.name         , None)
		self.assertEqual(f.none         , True)
		self.assertEqual(f.pk           , False)
		self.assertEqual(f.autoincrement, False)

		f = Datetime('creation')
		self.assertEqual(f.name          , 'creation')

		f = Datetime('creation', False, True)
		self.assertEqual(f.name         , 'creation')
		self.assertEqual(f.none         , False)
		self.assertEqual(f.pk           , True)

		f = Datetime(name='creation', allow_none=False, pk=True)
		self.assertEqual(f.name         , 'creation')
		self.assertEqual(f.none         , False)
		self.assertEqual(f.pk           , True)
	
		# object can't be None if pk is True	
		f = Datetime(allow_none=True, pk=True)
		self.assertEqual(f.none         , False)
		self.assertEqual(f.pk           , True)
	
		# default value	
		f = Datetime(default=datetime(1980, 04, 25))
		self.assertTrue(isinstance(f.default(), datetime))	
		self.assertEqual(f.default(), datetime(1980, 04, 25))

		f = Datetime(default='now')
		self.assertEqual(f.default().strftime("%Y/%m/%d"), datetime.now().strftime("%Y/%m/%d"))

		# cast:: not implemented yet
		# check:: not implemented yet

"""
r = Reference(i, 'zz')
print 'r=', r

r2 = ReferenceSet(s, 'tt')
print 'r2=', r2
"""
if __name__ == '__main__':
	unittest.main()
