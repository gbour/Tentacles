
import new
from datetime import datetime
from tentacles import Object
from tentacles import fields

#import orm.fields as base
class Field(object):
	sql_type = ''

	def sql_protect(self, value):
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
#		print 'Field::init', self
		pass
	
class Integer(Field):
	sql_type = 'INTEGER'
	
	def __init__(self):
		print 'SQINIT'

#	def sql_def(self):
#		# generic SQL definition
#		q = "%s INTEGER" % self.name
#		if self.pk:
#		   q += " PRIMARY KEY"

#		return q
		
#	def sql_name(self):
#		return 'ZZ'

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
	
class Datetime(String):
	sql_type = 'TEXT'
	
	def sql_protect(self, value):
		dt = value
		
		if value == 'now':
			dt = datetime.now()
			
		return dt.strftime("\"%Y/%m/%d %H:%M:%S\"")
		
class Reference(Field):
	def sql_def(self):
		q = self.name
		
		if len(self.remote[0].__pk__) > 1:
			raise Exception("can't reference an Object with multi-fields primary key")
		if len(self.remote[0].__pk__) == 0:
			raise Exception("can't reference an Object without  primary key")


		q += " FOREIGN KEY REFERENCES ("
		for pk in self.remote[0].__pk__:
		    q += "%s.%s," % (self.remote[0].__stor_name__, pk.name)
		q = q[:-1] + ")"

		return q

	def serialize(self, value):
		return getattr(value, value.__pk__[0].name)


JOIN_COUNT = 0

class ReferenceSet(Field):
#	@staticmethod
	def __backend_init__(self):
		"""We instanciate join table
		"""
#		print '>> backend::init=', self, self.reverse, self.sibling, self.remote
#		print self, dir(self)
		if not isinstance(self.sibling, fields.ReferenceSet) or self.reverse:
			return

		global JOIN_COUNT
		JOIN_COUNT += 1

		self.__obj_name__ = "join%03d__%s_%s" % \
			(JOIN_COUNT, self.__owner__.__stor_name__, self.name)
#		self.sibling.__obj_name__ = self.__obj_name__
		
		dct = {
			'__obj_name__': self.__obj_name__,
			'__refs__': {self.__owner__: [], self.remote: []}
		}


		for pk in self.__owner__.__pk__:
			r = fields.Reference(self.__owner__, pk=True)
			r.__auto__ = True

			dct["%s__%s" % (self.__owner__.__stor_name__, pk.name)] = r

		for pk in self.sibling.__owner__.__pk__:
			r = fields.Reference(self.sibling.__owner__, pk=True)
			r.__auto__ = True

			dct["%s__%s" % (self.sibling.__owner__.__stor_name__, pk.name)] = r

			join = new.classobj('Join%03d__%s_%s' % (JOIN_COUNT, self.__owner__.__stor_name__, self.name), 
				(Object,), dct)



	def sql_def(self):
		raise Exception("May not happend")

	def serialize(self):
		raise Exception('May not happend')

#	@classmethod
#	def init(cls):
#		print 'RefSet::init', cls, dir(cls)
