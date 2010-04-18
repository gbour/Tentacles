
import sys, re, inspect, types

class Uri(object):
	def __init__(self, raw):
		m = re.match('^(?P<scheme>\w+):(//((?P<username>[\w]+):(?P<password>[\w]+)@)?(?P<host>[\w.]+)(?P<port>\d+)?/)?(?P<db>[\w/.]+)', raw, re.U|re.L)
	
		for k, v in m.groupdict().iteritems():
			setattr(self, k, v)

class Database(object):
	__instance__  = None
	__tables__    = {}

	def __init__(self, uri):
		self.uri = Uri(uri)
		
		modname = "tentacles.backends.%s" % self.uri.scheme
		if not sys.modules.has_key(modname):
			raise Exception("Unknown '%s' database backend" % self.uri.scheme)
		
		exec "from %s import *" % modname
		if not hasattr(sys.modules[modname], 'Database'):
			raise Exception("Unknown '%s' database backend" % self.uri.scheme)

		backend = getattr(sys.modules[modname], 'Database')
		for name, obj in inspect.getmembers(backend):
			if name.startswith('__') or hasattr(self, name):
				continue
				
			if isinstance(obj, types.MethodType):
				obj = types.MethodType(obj.im_func, self)
			setattr(self, name, obj)
		
		for table in self.__tables__.itervalues():
			table.__inherit__(self)

		self.__class__.__instance__ = self
		
	@classmethod
	def register_table(cls, table):
		"""Register tables for this database.

			Tables register once themselves at definition time (metaclass.__init__)
		"""
		cls.__tables__[table.__table_name__] = table

		if cls.__instance__:
			table.__inherit__(cls.__instance__)

	def create_tables(self):
		for table in Database.__tables__.itervalues():
			table.create()
