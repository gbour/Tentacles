
from tentacles          import Storage
#from tentacles.lazy     import Ghost

class RefList(object):
	def __init__(self): #, owner, name, target):
#		self.__owner__    = owner
#		self.__name__     = name
#		self.__target__   = target                 # (object instance, fieldname) tuple

		self.__items__    = []

		# tracking changes
		self.__added__    = []
		self.__removed__  = []

	def __append__(self, value):
		if value in self.__items__:
			return False

		self.__items__.append(value)
		if value in self.__removed__:
			self.__removed__.remove(value)
		else:
			self.__added__.append(value)
#			print type(self.__owner__), dir(self.__owner__)
			self.__owner__.__dict__['__changed__'] = True

		return True

	def __remove__(self, value):
#		print 'rem:', self.__items__, self.__added__, value
		self.__items__.remove(value) # raise ValueError if not found
		if value in self.__added__:
			self.__added__.remove(value)
		else:
			self.__removed__.append(value)
			self.__owner__.__dict__['__changed__'] = True

	def __delitem__(self, i):
		value = self.__items__[i] # raise IndexError if not ranged
		
		del self.__items__[i]
		if value in self.__added__:
			self.__added__.remove(value)
		else:
			self.__removed__.append(value)
			self.__owner__.__changed__ = True

		return value

	def __len__(self):
		return len(self.__items__)

	def __str__(self):
		return str(self.__items__)

	def __repr__(self):
		return self.__str__()

	def has_changed(self):
		return(len(self.__added__) > 0 or len(self.__removed__) > 0)

	def saved(self):
		return False

	def save(self):
		raise Exception('NoOp')

	def __extend__(self, seq):
		for item in seq:
			self.__append__(item)

	def extend(self, seq):
		for item in seq:
			self.append(item)

	def __getitem__(self, num):
		item = self.__items__[num]

		from tentacles.lazy import Ghost
		if isinstance(item, Ghost):
			item = item.load()[0]
			self.__items__[num] = item

		return item

class o2m_RefList(RefList):
	"""
	"""
	def append(self, value):
		if self.__append__(value):
			# propagate 
			setattr(value, self.__target__[1], self.__owner__)

	def remove(self, value):
		self.__remove__(value)

		setattr(value, self.__target__[1], None)

	def __delitem__(self, i):
		value = super(o2m_RefList, self).__delitem__(i)

		setattr(value, self.__target__[1], None)

	def save(self):
#		print 'o2m::SAVE'
		for obj in self.__added__:
			obj.save()

		for obj in self.__removed__:
			obj.save()
		
		del self.__added__[:]
		del self.__removed__[:]


class m2m_RefList(RefList):
	def __init__(self, reverse=False, sibling=None):
		super(m2m_RefList, self).__init__()

		self.reverse = reverse
		self.sibling = sibling

	def append(self, value):
		if self.__append__(value):
			# propagate
			getattr(value, self.__target__[1]).__append__(self.__owner__)

	def remove(self, value):
		self.__remove__(value)

		getattr(value, self.__target__[1]).__remove__(self.__owner__)

	def __delitem__(self, i):
		value = super(m2m_RefList, self).__delitem__(i)

		getattr(value, self.__target__[1]).__remove__(self.__owner__)

	def saved(self):
		return True
		
	def save(self):
#		print 'm2m::save', self.__owner__, self.__name__, self.reverse
		for obj in self.__added__:
#			print '  .', obj
			obj.save()

		for obj in self.__removed__:
#			print obj
			obj.save()

#		print 'reverse=', self.reverse
		if not self.reverse:
			fld = self.__owner__.__fields__[self.__name__]
			q = "INSERT INTO %s VALUES (?, ?)" % fld.__obj_name__
			for obj in self.__added__:
				v = [getattr(self.__owner__, self.__owner__.__pk__[0].name), getattr(obj, obj.__pk__[0].name)]
#				print q, v
				Storage.__instance__.execute(q, v)

			q = "DELETE FROM %s WHERE %s__%s = ? AND %s__%s  = ?" % \
				(fld.__obj_name__, self.__owner__.__stor_name__, self.__owner__.__pk__[0].name, 
				self.sibling.__owner__.__stor_name__, self.sibling.__owner__.__pk__[0].name)

			for obj in self.__removed__:
				v = [getattr(self.__owner__, self.__owner__.__pk__[0].name), getattr(obj, obj.__pk__[0].name)]
#				print q, v
				Storage.__instance__.execute(q, v)



#		print 'STORAGE=', dir(Storage.__instance__)
		del self.__added__[:]
		del self.__removed__[:]



