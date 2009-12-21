==============
LodgeIt Readme
==============

Lodgeit implements a pastebin and some scripts to paste the service.


Installation
~~~~~~~~~~~~

LodgeIt requires at least Python 2.5 to work correctly. Next to this LodgeIt has
quite a few of dependencies as well as a nice bootstrap process. This is documentated
on the following slides.

Dependencies and virtual environment
====================================

To get LodgeIt work properly we need those dependencies: Python (at least 2.5),
python-setuptools and mercurial.

For Ubuntu (or any Debian based distribution) use ``aptitude`` to install::

    aptitude install python-dev python-setuptools python-virtualenv mercurial

Now we can install LodgeIt. But first we need to check out LodgeIt from the
mercurial repository. To do that you create a new folder ``lodgeit-dev`` in your
projects directory and change into it. There we initialize the virtual
environment and check out LodgeIt (main branch)::

	hg clone http://dev.pocoo.org/hg/lodgeit-main lodgeit

Right before we can initialize the virtual environment we need to install some
development packages to compile the python imaging library.

For Ubuntu again ``aptitude`` (as root)::

    sudo aptitude install build-essential
    apt-get build-dep python-imaging

Now it's possible to install the virtual environment. This is done with a simple
Python command::

    # assumed that you are located in lodgeit-dev/lodgeit
    python scripts/make-bootstrap.py > ../bootstrap.py
    cd ..
    # make sure that the virtualenv is not activated. If yes, execute `deactivate`
    python bootstrap.py .

You are ready to run now.

Database and other things
=========================

We are now ready to enter the virtual environment (assumed you are located in
``lodgeit-dev/lodgeit``)::

    . ../bin/activate

LodgeIt initializes it's database per default on /tmp/lodgeit.db, you can change
that path in the manage.py by modifiing ``dburi``.

Now start the development server::

    python manage runserver

Enjoy!
