
import sys, re, inspect, types

REFORDER = 0

class Uri(object):
	def __init__(self, raw):
		m = re.match('^(?P<scheme>\w+):(//((?P<username>[\w]+):(?P<password>[\w]+)@)?(?P<host>[\w.]+)(?P<port>\d+)?/)?(?P<db>[\w/.]+)', raw, re.U|re.L)
	
		for k, v in m.groupdict().iteritems():
			setattr(self, k, v)

class Storage(object):
	__instance__  = None
	__objects__   = []
	__refs__      = []
	__context__   = None

	def __init__(self, uri):
		self.uri = Uri(uri)
		
		modname = "tentacles.backends.%s" % self.uri.scheme
		if not sys.modules.has_key(modname):
			raise Exception("Unknown '%s' database backend" % self.uri.scheme)
		
		exec "from %s import *" % modname
		if not hasattr(sys.modules[modname], 'Storage'):
			raise Exception("Unknown '%s' storage backend" % self.uri.scheme)

		backend = getattr(sys.modules[modname], 'Storage')
		for name, obj in inspect.getmembers(backend):
			if name.startswith('__') or hasattr(self, name):
				continue
				
			if isinstance(obj, types.MethodType):
				obj = types.MethodType(obj.im_func, self)
			setattr(self, name, obj)
		
		self.__class__.__instance__ = self


	@classmethod
	def set_context(cls, name):
		@classmethod
		def _set_context(cls, obj):
		    obj.__stor_name__ = '%s_%s' % (name, obj.__stor_name__)
		
		if isinstance(name, types.FunctionType):
		    cls.__context__ = types.MethodType(name, cls, cls)
		else:
		    cls.__context__ = _set_context
	
	@classmethod
	def register(cls, obj):
		"""Register objects for this storage.

			Objects register once themselves at definition time (metaclass.__init__)
		"""
		if cls.__context__:
		    cls.__context__(obj)
		cls.__objects__.append(obj)

		if cls.__instance__:
			obj.__inherit__(cls.__instance__)

		# create extra tables
		# NOTE: delete cls.__refs__ to prevent infinite loop
#		refs = cls.__refs__
#		cls.__refs__ = []
#		for ref in refs:
#			cls.create_ref_table(ref)

#	@classmethod
#	def register_reference(cls, ref):
#		cls.__refs__.append(ref)

	def create_tables(self):
		for table in Database.__tables__:
			print table.create()
			
#	@classmethod
#	def create_ref_table(cls, ref):
#		import new
#		from tentacles import Table
#		from tentacles.fields import Reference
#		
#		global REFORDER
#		REFORDER += 1

#		dct = {
#			'__table_name__': "join%03d__%s__%s" % \
#				(REFORDER, ref.__owner__.__table_name__, ref.remote.__table_name__),
#			'__refs__': {ref.__owner__: [], ref.remote: []}
#		}
#		
#		for pk in ref.__owner__.__pk__:
#		    dct["%s__%s" % (ref.__owner__.__table_name__, pk.name)] = Reference(ref.__owner__, primary_key=True)
#		    dct['__refs__'][ref.__owner__].append((
#		        dct["%s__%s" % (ref.__owner__.__table_name__, pk.name)],
#		        pk))
#		for pk in ref.remote.__pk__:
#		    dct["%s__%s" % (ref.remote.__table_name__, pk.name)]    = Reference(ref.remote, primary_key=True)
#		    dct['__refs__'][ref.remote].append((
#		        dct["%s__%s" % (ref.remote.__table_name__, pk.name)],
#		        pk))

#		r = new.classobj('TableRef%03d__%s__%s' % (REFORDER, ref.__owner__.__name__, ref.remote.__name__), (Table,), dct)
#		ref.remote = r # owner


