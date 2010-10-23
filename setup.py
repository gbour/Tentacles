#!/usr/bin/env python

__version__ = "$Revision$ $Date$"

from distutils.core import setup

setup(
	name         = 'tentacles',
	version      = '0.1.0',
	description  = 'ORM',
	author       = 'Guillaume Bour',
	author_email = 'guillaume@bour.cc',
	url          = 'http://devedge.bour.cc/wiki/Tentacles/',
	license      = 'Affero',
	classifiers  = [],

	packages=['tentacles', 'tentacles.backends.sqlite3'],
	requires=['odict', 'reblok'],
)
