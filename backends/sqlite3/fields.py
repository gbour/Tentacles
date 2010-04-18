
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
        
#    def sql_def(self):
#        # generic SQL definition
#        q = "%s INTEGER" % self.name
#        if self.pk:
#           q += " PRIMARY KEY"

#        return q
        
#    def sql_name(self):
#        return 'ZZ'

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
        return "%s FOREIGN KEY REFERENCES (%s.id)" % (self.name, self.remote.__name__)

class ReferenceSet(Reference):
    def sql_def(self):
        return "%s FOREIGN KEY REFERENCES (%s_%s.%s_id)" % \
            (self.name, self.owner.__class__.__name__, self.remote.__name__, self.owner.__class__.__name__)

    def sql_extra(self):
        return 'CREATE TABLE'
