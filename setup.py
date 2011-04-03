#!/usr/bin/env python

__version__ = "$Revision$ $Date$"

from distutils.core import setup

setup(
	name         = 'tentacles',
	version      = '0.1.0',
	description  = 'Object-Relational Model (ORM)',
	author       = 'Guillaume Bour',
	author_email = 'guillaume@bour.cc',
	url          = 'http://devedge.bour.cc/wiki/Tentacles',
	license      = 'GNU Affero General Public License v3',
	classifiers  = [
		'Development Status :: 3 - Alpha',
		'Environment :: Console',
		'Environment :: No Input/Output (Daemon)',
		'Environment :: Web Environment',
		'Environment :: X11 Applications',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: GNU Affero General Public License v3',
		'Natural Language :: English',
		'Natural Language :: French',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Programming Language :: Python :: 2.5',
		'Programming Language :: Python :: 2.6',
		'Programming Language :: Python :: 2.7',
		'Topic :: Database',
		'Topic :: Internet',
		'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
		'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
		'Topic :: Software Development',
		'Topic :: Software Development :: Libraries :: Application Frameworks',
		'Topic :: Software Development :: Libraries :: Python Modules',
	],

	long_description = """Tentacles is a python ORM.
	The main idea is to manipulate stored datas as you do for python data structures

	python native	
	>>> class SuperHero(object):
	>>>		def __init__(self, name, gender, power):
	>>>			self.name   = name
	>>>			self.gender = gender
	>>>			self.power  = power
	>>>
	>>> hero1 = SuperHero('superman', 'male', 'flight')
	>>> print "%s can %s" % (hero1.name, hero1.power)

	... vs ...

	tentacles
	>>> from tentacles        import Object
	>>> from tentacles.fields import *
	>>> class SuperHero(Object):
	>>>		name   = String()
	>>> 	gender = String()
	>>> 	power  = String()
	>>>
	>>> hero1 = SuperHero(name='superman', gender='male', power='flight')
	>>> print "%s can %s" % (hero1.name, hero1.power)


	python native
	>>> heros   = [hero1, SuperHero(name='wonder woman', gender='female', power='enhanced vision')]
	>>> females = filter(lambda e: e.gender = 'female', heros)
	>>> for e in females:
	>>> 	print "superheroine: %s" % e.name

	... vs ...

	tentacles
	>>> hero1.save(); SuperHero(name='wonder woman', gender='female', power='enhanced vision').save()
	>>> females = filter(lambda e: e.gender = 'female', heros)
	>>> for e in females:
	>>> 	print "superheroine: %s" % e.name

	Tentacles is pretty yound and incomplete, and still in alpha stage.
	It currently support only sqlite3 backend, while more are scheduled at mid-term (mysql, postgresql, but also no-sql storages, like openldap, mongodb, ...)
	""",


	packages=['tentacles', 'tentacles.backends.sqlite3'],
	data_files=[('share/doc/python-tentacles', ('README.md','AUTHORS','COPYING'))],
	requires=['odict', 'reblok'],
)
