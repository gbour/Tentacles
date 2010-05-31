#!/usr/bin/env python

__version__ = "$Revision$ $Date$"

from distutils.core import setup

setup(
	name         = 'tentacles',
	version      = '0.1.0',
	description  = 'Python ORM',
	author       = 'Guillaume Bour',
	author_email = 'guillaume@bour.cc',
	url          = 'http://devedge.bour.cc/wiki/Tentacles/',
	licence      = 'GPL v3',

	packages=['tentacles', 'tentacles.backends', 'tentacles.backends.sqlite3'],
)
