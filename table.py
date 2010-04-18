
import orm, inspect, types, sys
from orm.fields import Field, FieldDescription, ReferenceSet

class MetaTable(type):
    def __init__(cls, name, bases, dct):
        #print 'MetaTable:', name, bases, dct
        for k, v in dct.iteritems():
            if isinstance(v, FieldDescription) and issubclass(v.klass, ReferenceSet):
                print k, v.klass
                dct[k] = JoinTableDescription(v.klass, v.kwargs['remote'])

        print dct
        orm.Database.register_table(cls)
        return super(MetaTable, cls).__init__(name, bases, dct)

class Table(object):
    __metaclass__ = MetaTable

    def __new__(cls, *args, **kwargs):
        print 'NEW TABLE'
        db   = kwargs['database'] if 'database' in kwargs else orm.__DATABASE__
        
        inst = super(Table, cls).__new__(cls, *args, **kwargs)

        modname = "orm.backends.%s" % db.uri.scheme
        exec "from %s import *" % modname
        inst.__dbtable__ = getattr(sys.modules[modname], 'Table')

        for name, obj in inspect.getmembers(inst.__dbtable__):
            if name.startswith('__'):
                continue

            if isinstance(obj, types.MethodType):
                obj = types.MethodType(obj.im_func, inst)

            setattr(inst, name, obj)

        return inst

    def __init__(self, *args, **kwargs):
        # apply dbtable constructor on self
        fnc = types.MethodType(self.__dbtable__.__init__.im_func, self, self.__class__)
        fnc(self, *args, **kwargs)
        
        # instanciate Field attributes
        self.db   = kwargs['database'] if 'database' in kwargs else orm.__DATABASE__

        self.__fields__ = []
        for name, obj in inspect.getmembers(self):
            if isinstance(obj, FieldDescription):
                _kwargs = obj.kwargs
                _kwargs['name']     = name
                _kwargs['database'] = self.db
                _kwargs['order']    = obj.order
                _kwargs['owner']    = self
            
#                print obj.klass, obj.args, _kwargs
                fld = obj.klass(*obj.args, **_kwargs)
                self.__fields__.append(fld)
                setattr(self, name, fld)
                
        self.__fields__.sort(lambda x, y: x.order - y.order)

class JoinTableDescription(object):
	def __init__(self, src , dst):
		self.src   = src
		self.dst   = dst
