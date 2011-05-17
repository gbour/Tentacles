# -*- coding: utf8 -*-
"""
    tentacles, python ORM
    Copyright (C) 2010-2011, Guillaume Bour <guillaume@bour.cc>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 3.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
__author__  = "Guillaume Bour <guillaume@bour.cc>"
__version__ = "$Revision$"
__date__    = "$Date$"

from tentacles          import Storage


class RefList(object):
	"""List of references with tracking-changes memory

		internal fields:
		* __owner__    = owner
		* __target__   = values allowed in the RefList. *(ObjectClass, fieldname)* tuple
										 (also used to propagate changes)
#		self.__name__     = name
	"""

	def __init__(self):
		self.__items__    = []

		# tracking changes
		self.__added__    = []
		self.__removed__  = []

	def __append__(self, value):
		"""Add *value* to the RefList
	
			NOTE: we cannot add twice the same value (return *False* if object already in list)
		"""
		if value in self.__items__:
			return False

		self.__items__.append(value)
		if value in self.__removed__:
			self.__removed__.remove(value)
		else:
			self.__added__.append(value)
			#TODO: we should send a signal instead of directly modifying value
			self.__owner__.__dict__['__changed__'] = True

		return True

	def __remove__(self, value):
		self.__items__.remove(value) # raise ValueError if not found
		if value in self.__added__:
			self.__added__.remove(value)
		else:
			self.__removed__.append(value)
			#TODO: send signal
			self.__owner__.__dict__['__changed__'] = True

	def __delitem__(self, i):
		value = self.__items__[i] # raise IndexError if not ranged
		
		del self.__items__[i]
		if value in self.__added__:
			self.__added__.remove(value)
		else:
			self.__removed__.append(value)
			#TODO: send signal
			self.__owner__.__dict__['__changed__'] = True

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
		"""Private extend.
		
			May not be called by external program
			bypass «changes tracking» mechanism
		"""
		self.__items__.extend(seq)

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
		
	def clear(self):
		# we must make a copy because we modify the list during its enumeration
		for item in list(self.__items__):
			self.remove(item)


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
		for obj in self.__added__:
			obj.save()

		for obj in self.__removed__:
			obj.save()
		
		del self.__added__[:]
		del self.__removed__[:]


class m2m_RefList(RefList):
	"""many2many reference list

		User										Group
			. memberof	  * - *			. members

		a User is _memberof_ many groups
		a Group as many _members_
	"""
	def __init__(self, reverse=False, sibling=None):
		super(m2m_RefList, self).__init__()

		self.reverse = reverse
		self.sibling = sibling

	def append(self, value):
		"""Append object to the reflist
		"""
		if self.__append__(value):
			# propagate
			getattr(value, self.__target__[1]).__append__(self.__owner__)

	def remove(self, value):
		"""Remove object from reflist
		"""
		self.__remove__(value)
		getattr(value, self.__target__[1]).__remove__(self.__owner__)

	def __delitem__(self, i):
		value = super(m2m_RefList, self).__delitem__(i)

		from tentacles.lazy import Ghost
		if isinstance(value, Ghost):
			value = value.load()#cache_only=True)
			if value is not None:
				value = value[0]

		if value is not None:
			getattr(value, self.__target__[1]).__remove__(self.__owner__)

	def saved(self):
		if self.reverse:
			return True
		
		# TODO: check self.__added__ and self.__removed__
		return False
		
	def save(self):
		"""
		"""
		for obj in self.__added__:
			obj.save()

		for obj in self.__removed__:
			obj.save()

#		print "saved ?", self.__owner__, self.__owner__.saved()
		if not self.__owner__.saved():
			return

		#TODO: SQL code MUST be exported in specific backends implementations
		if not self.reverse:
			fld = self.__owner__.__fields__[self.__name__]
			q = "INSERT INTO %s VALUES (?, ?)" % fld.__stor_name__
			for obj in self.__added__:
				v = [getattr(self.__owner__, self.__owner__.__pk__[0].name), getattr(obj, obj.__pk__[0].name)]
				Storage.__instance__.execute(q, v)

			q = "DELETE FROM %s WHERE %s__%s = ? AND %s__%s  = ?" % \
				(fld.__stor_name__, self.__owner__.__stor_name__, self.__owner__.__pk__[0].name, 
				self.sibling.__owner__.__stor_name__, self.sibling.__owner__.__pk__[0].name)

			for obj in self.__removed__:
				v = [getattr(self.__owner__, self.__owner__.__pk__[0].name), getattr(obj, obj.__pk__[0].name)]
				Storage.__instance__.execute(q, v)

		del self.__added__[:]
		del self.__removed__[:]

