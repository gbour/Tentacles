import sqlite3, new
from tentacles import Object
from tentacles.fields import Reference, ReferenceSet

REFORDER = 1

class SQLiteStorage(object):
    def __init__(self, uri):
        self.uri = uri
        self.db = sqlite3.connect(uri.db)
        
    def execute(self, query):
        res = self.db.execute(query)

    def create_join_table(self, ref):
        """
          cannot be private or will not be inherited
        """
        if ref.reverse:
            ref = ref.sibling

        # creating an hidden join table
        global REFORDER
        REFORDER += 1

        dct = {
            '__obj_name__': "join%03d__%s_%s" % \
                (REFORDER, ref.__owner__.__stor_name__, ref.name),
            '__refs__': {ref.__owner__: [], ref.remote: []}
        }

        for pk in ref.__owner__.__pk__:
            r = Reference(ref.__owner__, pk=True)
            r.__auto__ = True
            
            dct["%s__%s" % (ref.__owner__.__stor_name__, pk.name)] = r
#            dct['__refs__'][ref.__owner__].append((
#		        dct["%s__%s" % (ref.__owner__.__table_name__, pk.name)],
#		        pk))

        for pk in ref.sibling.__owner__.__pk__:
            r = Reference(ref.sibling.__owner__, pk=True)
            r.__auto__ = True
            
            dct["%s__%s" % (ref.sibling.__owner__.__stor_name__, pk.name)] = r

#		for pk in ref.remote.__pk__:
#		    dct["%s__%s" % (ref.remote.__table_name__, pk.name)]    = Reference(ref.remote, primary_key=True)
#		    dct['__refs__'][ref.remote].append((
#		        dct["%s__%s" % (ref.remote.__table_name__, pk.name)],
#		        pk))

        join = new.classobj('Join%03d__%s_%s' % (REFORDER, ref.__owner__.__stor_name__, ref.name), 
            (Object,), dct)
        self.__objects__.remove(join)

        ref.__hidden__         = True
        ref.sibling.__hidden__ = True

        return join

    def create(self):
        refs = []
        for obj in self.__objects__:
            for ref in obj.__refs__:
                if ref in refs or ref.sibling in refs or not isinstance(ref, ReferenceSet) or not isinstance(ref.sibling, ReferenceSet):
                    continue

                join = self.create_join_table(ref)
                print join.create()
                refs.append(ref); refs.append(ref.sibling)

            print obj.create()
