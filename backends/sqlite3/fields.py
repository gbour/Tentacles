
from datetime import datetime

#import orm.fields as base
class Field(object):
	sql_type = ''

	def sql_protect(self, value):
		return value

	def sql_def(self):
		return "%s %s" % (self.name, self.sql_type)

	def sql_extra(self):
		return ''

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

class ReferenceSet(Field):
	def sql_def(self):
		raise Exception("May not happend")

