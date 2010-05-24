from tentacles.fields import ReferenceSet

class Ghost(object):
	def __init__(self, owner, field, target, pks):
		self.__owner__  = owner
		self.__field__  = field
		
		self.__target__ = target
		self.__pks__    = pks

	def load(self):
#		print 'Ghost::load>', self.__owner__, self.__field__, self.__pks__
		kwargs = self.__pks__.copy()
		kwargs['lazy']  = False
		kwargs['owner'] = self.__owner__
		
#		print self.__field__, self.__target__
		if isinstance(self.__field__, ReferenceSet):
			# internally called =>  no args
			value = self.__field__.get(**kwargs)
		else:
			value = self.__target__.get(**kwargs)

		return value

	def __str__(self):
		return "Ghost(%s=%s)" % (self.__target__.__name__, self.__pks__)

	def __repr__(self):
		return str(self)
