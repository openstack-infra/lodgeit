from nose import with_setup

from lodgeit.application import db, make_app
from lodgeit.models import Paste

foo = make_app('sqlite://', 'NONE', False, True)


def setup():
    pass


def teardown():
    Paste.query.delete()
    db.session.commit()
    db.session.remove()


def testcase():
    def dec(f):
        return with_setup(setup, teardown)(f)
    return dec


testcase.__test__ = False
