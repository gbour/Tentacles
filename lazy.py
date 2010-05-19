
class Ghost(object):
	def __init__(self, target, pks):
		self.__target__ = target
		self.__pks__    = pks

	def load(self):
		kwargs = self.__pks__.copy()
		kwargs['lazy'] = False
		print 'load', kwargs
		return self.__target__.get(**kwargs)

	def __str__(self):
		return "Ghost(%s=%s)" % (self.__target__.__name__, self.__pks__)

	def __repr__(self):
		return str(self)
