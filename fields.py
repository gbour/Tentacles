# -*- coding: utf8 -*-

import inspect, types, sys
import orm

ORDER = 0
class FieldDescription(object):
    def __init__(self, klass, args, kwargs):
        global ORDER 
        self.order  = ORDER
        ORDER += 1
        
        self.klass  = klass
        self.args   = args
        self.kwargs = kwargs

#class ReferenceDescription(FieldDescription):
        
#        print dir(sys.modules['__main__'])
#        print sys.modules.keys()
    
class Field(object):
    type = types.NoneType
    isfield = True

    def __new__(cls, *args, **kwargs):
        # Table fields must be instanciated only after table is instanciated
        # (so take the correct database value)
        if 'database' not in kwargs:
            if issubclass(cls, Reference):
                 kwargs['remote'] = args[0]
                 args = ()
#                return ReferenceDescription(cls, args, kwargs)
            return FieldDescription(cls, args, kwargs)
            
        inst = super(Field, cls).__new__(cls, *args, **kwargs)
        db = kwargs['database']
        modname = "orm.backends.%s" % db.uri.scheme
        exec "from %s import *" % modname

        dbfield = getattr(sys.modules[modname], cls.__name__)
#        print 'dbfield=', dbfield

        for name, obj in inspect.getmembers(dbfield):
            if name.startswith('__'):
                continue

            if isinstance(obj, types.MethodType):
                obj = types.MethodType(obj.im_func, inst)

            setattr(inst, name, obj)

        return inst

    def __init__(self, name=None, notnull=False, primary_key=False, database=None, order=-1, **kwargs):
        self.name       = name
        self.notnull    = notnull
        self.pk         = primary_key
        self.order      = order
        self.unique     = False
        
        if 'default' in kwargs:
            self.default   = kwargs['default']
        if 'remote' in kwargs:
            self.remote    = kwargs['remote']
        if 'owner' in kwargs:
            self.owner    = kwargs['owner']

#        self.database   = database if database else orm.__DATABASE__
#        
#        modname = "%s.backends.%s" % (self.__module__.split('.', 1)[0], self.database.uri.scheme)
#        exec "from %s import *" % modname

#        try:
#            dbfield = eval("%s.%s()" % (modname, self.__class__.__name__))
#        except AttributeError:
#            raise Exception("*%s* type not defined in *%s* backend" % \
#                (self.__class__.__name__, self.database.uri.scheme))

#        for name, obj in inspect.getmembers(dbfield):
#            if name.startswith('__'):
#                continue

#            if isinstance(obj, types.MethodType):
#                obj = types.MethodType(obj.im_func, self)
#                
#            setattr(self, name, obj)


class Integer(Field):
    type = int

class String(Field):
    type = unicode

class Binary(Field):
    pass
    
class Boolean(Field):
    pass
    
class Datetime(Field):
    pass

class Reference(Field):
    pass
    
class ReferenceSet(Reference):
    pass
