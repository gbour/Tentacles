import inspect, types, StringIO, sqlite3
#from orm.fields import Field

class Table(object):
	sqlite3 = None

	def __init__(self, *args, **kwargs):
		self.zz = 22

	@classmethod
	def create(cls):
		print cls
		q = 'CREATE TABLE ' + cls.__table_name__ + ' ( \n'
		for fld in cls.__fields__:
		    print fld
		print q


#		for fld in self.__fields__:
#			q += " " + fld.sql_def()
##			q += "  %s %s" % (fld.name, fld.sql_type)
#			if fld.pk:
#			    q += " PRIMARY KEY"
#			if fld.unique:
#			    q += " UNIQUE"
#			if fld.notnull:
#			    q += " NOT NULL"
#			if hasattr(fld, 'default'):
#			    q += " DEFAULT"
#			    if fld.default is None:
#			        q += " NULL"
#			    else:
#			        q += " " + fld.sql_protect(fld.default)
#			    
#			    
#			q += ",\n"

#		q = q[:-2] + '\n)'
#		return q
#		
#	def sql_get(self):
#	    q = 'SELECT * FROM ' + self.__class__.__name__
#	    res = self.db.execute(q)
#	    print res
#	    
#	def sql_create(self):
#	    q = self.sql_def()
#	    print q
#	    self.db.execute(q)

