
import sys, re, inspect, types

class Uri(object):
    def __init__(self, raw):
        m = re.match('^(?P<scheme>\w+):(//((?P<username>[\w]+):(?P<password>[\w]+)@)?(?P<host>[\w.]+)(?P<port>\d+)?/)?(?P<db>[\w/.]+)', raw, re.U|re.L)
    
        for k, v in m.groupdict().iteritems():
            setattr(self, k, v)

class Database(object):
    __tables__ = {}

    def __init__(self, uri, setglobal=True):
        self.uri = Uri(uri)
        
        modname = "%s.backends.%s" % (self.__module__.rsplit('.', 1)[0], self.uri.scheme)
        if not sys.modules.has_key(modname):
            raise Exception("Unknown '%s' database backend" % uri.scheme)
        
        exec "from %s import *" % modname
        sdb = SQLiteDatabase(self.uri)
        
        for name, obj in inspect.getmembers(sdb):
            if name.startswith('__'):
                continue
                
            if isinstance(obj, types.MethodType):
                obj = types.MethodType(obj.im_func, self)
            setattr(self, name, obj)
            
        if setglobal:
            sys.modules[self.__module__.split('.', 1)[0]].__DATABASE__ = self
        
    def toto(self):
        print "Database::toto"
        
        
    @staticmethod
    def register_table(table):
        Database.__tables__[table.__name__] = table

    def create_tables(self):
        for table in Database.__tables__.itervalues():
            print table
