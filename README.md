Tentacles
=========

Tentacles is a Object-Relational Model (ORM) written in Python.
It's main concept is to manipulate stored datas as you do for python data structures.

###Requirements
* odict (can be found on [pypi](pypi.python.org))
* [Reblok](http://devedge.bour/cc/wiki/Reblok)

###Installation
To install:

	easy_install tentacles

or

	wget [http://devedge.bour.cc/resources/tentacles/src/tentacles.latest.tar.gz](http://devedge.bour.cc/resources/tentacles/src/tentacles.latest.tar.gz)
	tar xvf tentacles.latest.tar.gz
	cd tentacles-* && ./setup.py install


Python native datas manipulation vs tentacles
---------------------------------------------

python **native**

	class SuperHero(object):
		def __init__(self, name, gender, power):
			self.name   = name
			self.gender = gender
			self.power  = power
	
	 hero1 = SuperHero('superman', 'male', 'flight')
	 print "%s can %s" % (hero1.name, hero1.power)

... vs **tentacles**

	from tentacles import Object
	from fields    import *
	class SuperHero(Object):
		name   = String()
		gender = String()
		power  = String()
	
	hero1 = SuperHero(name='superman', gender='male', power='flight')
	print "%s can %s" % (hero1.name, hero1.power)


python **native**

	heros   = [hero1, SuperHero(name='wonder woman', gender='female', power='enhanced vision')]
	females = filter(lambda e: e.gender == 'female', heros)
	for e in females:
		print "superheroine: %s" % e.name

... vs **tentacles**

	hero1.save()
	SuperHero(name='wonder woman', gender='female', power='enhanced vision').save()

	from tentacles import filter
	females = filter(lambda e: e.gender == 'female', SuperHero)
	for e in females:
		print "superheroine: %s" % e.name


Declaring Objects
-----------------

First, import requirements
	
	from tentacles        import *
	from tentacles.fields import *

Then open your datastorage (it creates the database if not exists)

	db = Storage('sqlite3:/tmp/test.db')

You can now declare your objects (inheriting from `Object` base class).
Each object is made of a list of typed fields:

	class User(Object):
		id 	    = Integer(pk=True, autoincrement=True)
		name    = String(default='John Doe')
		active  = Boolean(default=False)

	class Group(Object):
		id      = Integer(pk=True)
		name    = String()

		owner   = Reference(User)
		members = ReferenceSet(User)

Finally, create underlying Object stores:

	db.create()


Manipulating Objects
--------------------

Create Objects, setting default fields values

	john = User(name='jon', active=True)
	mary = User(name='mary', active=False)

	admins = Group(name='admins')

Reading and Writing Objects fields values

	print john.name
	>>> 'jon'

	john.name = 'john'

Relational fields (ReferenceSet field is manipulated just as a python list)

	admins.owner   = john
	admins.members = [john]

	admins.members.append(mary)

Saving Objects to underlying storage

	admins.save()


Querying Objects
----------------
Queying possibilities are currently limited

###Selection

	active_members = filter(lambda u: u.active == True, User)

###Range
	some_members   = User[10:20]

###Sorting
	alphabetic_members = User >> 'name'

**NOTE**: `>>` sort in ascending order while `<<̀  in descending

Of course, you can combine those queries:

	active_members = filter(lambda u: u.active == True, User)[10:20] >> 'name'


Available Field Types
---------------------

each field can take *default* and *unique* (boolean) parameters

###Integer
	A signed integer value

parameters:

* allow_none: allow field to take None value
* pk (boolean): if True, the field is the primary key of the object underlying table (**MUST** then be unique)
* autoincrement (boolean): if True, field value will be automatically set when saving, with an increasing value

	
###String
	An unlimit sized string value.

**NOTE**: strings are stored in unicode

###Boolean
	`True` or `False` value.

###Binary
	Any type of binary content (picture, file content, ...).

###Datetime
	A datetime value (should be an instance of `datetime.datetime`)i

**NOTE**: if default is `"now"`, empty value will be initialized with current datetime when data saved

###Reference
	Unary (e.g *one to many*) reference to another Object.

**NOTE**: requires the Object as first argument

	owner = Reference(User)

##ReferenceSet
	Multiple (e.g *many to many*) reference to another Object.

**NOTE**: requires the Object as first argument

	members = ReferenceSet(User)


Futures
-------

Tentacles is pretty yound and incomplete, and still in alpha stage.
It currently support only sqlite3 backend, while more are scheduled at mid-term (mysql, postgresql, but also no-sql storages, like openldap, mongodb, ...)


About
-----

*Tentacles* is licensed under GNU GPL v3.
It is written by Guillaume Bour <guillaume@bour.cc>
