from tentacles.fields import ReferenceSet

class Ghost(object):
	def __init__(self, owner, field, target, pks):
		self.__owner__  = owner
		self.__field__  = field
		
		self.__target__ = target
		self.__pks__    = pks

	def load(self, cache_only=False):
		kwargs = self.__pks__.copy()
		kwargs['lazy']       = False
		kwargs['owner']      = self.__owner__
		kwargs['cache_only'] = cache_only
		
		if isinstance(self.__field__, ReferenceSet):
			value = self.__field__.get(**kwargs)
		else:
			value = self.__target__.get(**kwargs)

		return value

	def __str__(self):
		return "Ghost(%s=%s)" % (self.__target__.__name__, self.__pks__)

	def __repr__(self):
		return str(self)
		
	def __eq__(self, other):
		from tentacles.table  import Object
		if isinstance(other, Object):
			return other.__class__ == self.__target__ and \
				self.__pks__.values()[0] == getattr(other, other.__pk__[0].name)
			
		return id(other) == id(self)

