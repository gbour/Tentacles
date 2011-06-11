#!/usr/bin/python
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
"""
	The power of superheros !!!

"""
from tentacles        import *
from tentacles.fields import *

# open or create storage
db = Storage('sqlite3::memory:')

class Power(Object):
	id     = Integer(pk=True, autoincrement=True)
	name   = String()

class SuperHero(Object):
	name   = String(pk=True)
	gender = String()
	power  = Reference(Power)
	
# create storage objects
db.create()

# simple test
superman = SuperHero(name='Superman', gender='male', power=Power(name='flight'))
print "%s can %s" % (superman.name, superman.power.name)

superman.save()


# create list of superheros
heros = [
	{
		'name'  : 'Aquaman',
		'gender': 'male',
		'power' : 'underwater breathing',
	},
	{
		'name'  : 'Elektra',
		'gender': 'female',
		'power' : None,
	},
	{
		'name'  : 'Doctor strange',
		'gender': 'male',
		'power' : 'telekinesis',
	},
	{
		'name'  : 'Daphne powel',
		'gender': 'female',
		'power' : 'telepathy',
	},
	{
		'name'  : 'Cannonball',
		'gender': 'male',
		'power' : 'superspeed',
	},
]

for h in heros:
	h['power'] = Power(name=h['power']) if h['power'] is not None else None
	SuperHero(**h).save()

# query superheros
subset = filter(lambda h: h.gender == 'male', SuperHero)[1:2] >> 'name'
print '\n', subset, '\n', list(subset)

print "\nSome male superheros:"
for h in subset:
	print " * %s (has '%s' power)" % (h.name, h.power.name)
