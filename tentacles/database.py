
import sys, re, inspect, types


class Uri(object):
	def __init__(self, raw):
		m = re.match('^(?P<scheme>\w+):(//((?P<username>[\w]+):(?P<password>[\w]+)@)?(?P<host>[\w.]+)(?P<port>\d+)?/)?(?P<db>[\w:/.]+)', raw, re.U|re.L)
	
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

		# call backend init method
		types.MethodType(backend.__init__.im_func, self)(self.uri)

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
