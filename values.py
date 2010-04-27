
class RefList(object):
	def __init__(self, owner, name, target):
		self.__owner__    = owner
		self.__name__     = name
		self.__target__   = target                 # object instance, fieldname

		self.__items__    = []

		# tracking changes
		self.__added__    = []
		self.__removed__  = []

	def __append__(self, value):
		self.__items__.append(value)
		if value in self.__removed__:
			self.__removed__.remove(value)
		else:
			self.__added__.append(value)
			self.__owner__.__changed__ = True

	def __remove__(self, value):
		self.__items__.remove(value) # raise ValueError if not found
		if value in self.__added__:
			self.__added__.remove(value)
		else:
			self.__removed__.add(value)
			self.__owner__.__changed__ = True

	def __delitem__(self, i):
		value = self.__items__[i] # raise IndexError if not ranged
		
		del self.__items__[i]
		if value in self.__added__:
			self.__added__.remove(value)
		else:
			self.__removed__.append(value)
			self.__owner__.__changed__ = True

class o2m_RefList(RefList):
	"""
	"""
	def append(self, value):
		self.__append__(value)

		# propagate 
		setattr(value, self.__target__[1], self.__owner__)

class m2m_RefList(RefList):
	def append(self, value):
		self.__append__(value)

		# propagate
		getattr(value, self.__target__[1]).__append__(self.__owner__)


#print '>>',z
#z = One2Many_RefList(None, None, None)
	
#		
#	def append(self, value):
#		"""Update internal sets
#		"""
#		self.__append__(value)

#		# propagate
#		if value.__dict__[self.__peer__]:
#			getattr(value.__dict__[self.__peer__], self.__fld__.name).remove(value)

#		value.__dict__[self.__peer__] = self.__owner__


#	def remove(self, value):
#		self.__remove__(value)




#	def __len__(self):
#		return len(self.__items__)

#	def save(self):
#		for itm in self.__added__:
#			itm.save()
#		del self.__added__[:]
#			
#		for itm in self.__removed__:
#			itm.save()
#		del self.__removed__[:]

#	def __unicode__(self):
#		return str(self.__items__)

#	def __str__(self):
#		return self.__unicode__()

#	def __repr__(self):
#		return self.__unicode__()


