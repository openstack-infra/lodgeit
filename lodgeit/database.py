# -*- coding: utf-8 -*-
"""
    lodgeit.database
    ~~~~~~~~~~~~~~~~

    Database fun :)

    :copyright: 2007-2010 by Armin Ronacher, Christopher Grebs.
    :license: BSD
"""
import sys
from types import ModuleType
import sqlalchemy
from sqlalchemy import MetaData, create_engine
from sqlalchemy import orm, sql
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import declarative_base
from lodgeit.local import application, _local_manager


metadata = MetaData()


def session_factory():
    opts = {
        'autoflush': True,
        'transactional': True}
    return orm.create_session(application.engine, **opts)
session = orm.scoped_session(
    session_factory, scopefunc=_local_manager.get_ident)


class ModelBase(object):
    """Internal baseclass for all models.  It provides some syntactic
    sugar and maps the default query property.

    We use the declarative model api from sqlalchemy.
    """


# configure the declarative base
Model = declarative_base(name='Model', cls=ModelBase,
    mapper=orm.mapper, metadata=metadata)
ModelBase.query = session.query_property()


def _make_module():
    db = ModuleType('db')
    for mod in sqlalchemy, orm:
        for key, value in mod.__dict__.iteritems():
            if key in mod.__all__:
                setattr(db, key, value)

    db.session = session
    db.metadata = metadata
    db.Model = Model
    db.NoResultFound = orm.exc.NoResultFound
    return db

sys.modules['lodgeit.database.db'] = db = _make_module()
