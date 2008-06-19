# -*- coding: utf-8 -*-
"""
    lodgeit.database
    ~~~~~~~~~~~~~~~~

    Database fun :)

    :copyright: 2007 by Armin Ronacher, Christopher Grebs.
    :license: BSD
"""
import time
import difflib
from types import ModuleType
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.orm.scoping import ScopedSession
from cgi import escape
from datetime import datetime
from lodgeit.utils import _local_manager, ctx
from lodgeit.lib.highlighting import highlight, LANGUAGES


def session_factory():
    return orm.create_session(bind=ctx.application.engine)

session = ScopedSession(session_factory, scopefunc=_local_manager.get_ident)

#: create a fake module for easy access to database session methods
db = ModuleType('db')
key = value = mod = None
for mod in sqlalchemy, orm:
    for key, value in mod.__dict__.iteritems():
        if key in mod.__all__:
            setattr(db, key, value)
del key, mod, value

db.__doc__ = __doc__
for name in 'delete', 'save', 'flush', 'execute', 'begin', 'query', \
            'commit', 'rollback', 'clear', 'refresh', 'expire':
    setattr(db, name, getattr(session, name))
db.session = session


metadata = db.MetaData()

pastes = db.Table('pastes', metadata,
    db.Column('paste_id', db.Integer, primary_key=True),
    db.Column('code', db.String),
    db.Column('parsed_code', db.String),
    db.Column('parent_id', db.Integer, db.ForeignKey('pastes.paste_id'),
                nullable=True),
    db.Column('pub_date', db.DateTime),
    db.Column('language', db.String(30)),
    db.Column('user_hash', db.String(40), nullable=True),
    db.Column('handled', db.Boolean, nullable=False)
)


spam_rules = db.Table('spam_rules', metadata,
    db.Column('rule_id', db.Integer, primary_key=True),
    db.Column('rule', db.String)
)



class Paste(object):

    def __init__(self, code, language, parent=None, user_hash=None):
        if language not in LANGUAGES:
            language = 'text'
        self.code = u'\n'.join(code.splitlines())
        self.language = language
        if isinstance(parent, Paste):
            self.parent = parent
        elif parent is not None:
            self.parent_id = parent
        self.pub_date = datetime.now()
        self.handled = False
        self.user_hash = user_hash

    @property
    def url(self):
        return '/show/%d/' % self.paste_id

    def compare_to(self, other, context_lines=4, template=False):
        udiff = u'\n'.join(difflib.unified_diff(
            self.code.splitlines(),
            other.code.splitlines(),
            fromfile='Paste #%d' % self.paste_id,
            tofile='Paste #%d' % other.paste_id,
            lineterm='',
            n=context_lines
        ))
        if template:
            from lodgeit.lib.diff import prepare_udiff
            rv = prepare_udiff(udiff)
            return rv and rv[0] or None
        return udiff

    def rehighlight(self, linenos=True):
        self.parsed_code = highlight(self.code, self.language, linenos)

    def to_xmlrpc_dict(self):
        from lodgeit.lib.xmlrpc import strip_control_chars
        return {
            'paste_id':         self.paste_id,
            'code':             strip_control_chars(self.code),
            'parsed_code':      strip_control_chars(self.parsed_code),
            'pub_date':         int(time.mktime(self.pub_date.timetuple())),
            'language':         self.language,
            'parent_id':        self.parent_id,
            'url':              self.url
        }

    def render_preview(self):
        try:
            start = self.parsed_code.index('</pre>')
            code = self.parsed_code[
                self.parsed_code.index('<pre>', start) + 5:
                self.parsed_code.rindex('</pre>')
            ].strip('\n').splitlines()
        except IndexError:
            code = self.code.strip('\n').splitlines()
        code = '\n'.join(code[:5] + ['...'])
        return '<pre class="syntax">%s</pre>' % code

    @staticmethod
    def fetch_replies():
        """
        Get the new replies for the ower of a request and flag them
        as handled.
        """
        s = db.select([pastes.c.paste_id],
            Paste.user_hash == ctx.request.user_hash
        )

        paste_list = db.session.query(Paste).filter(db.and_(
            Paste.parent_id.in_(s),
            Paste.handled == False,
            Paste.user_hash != ctx.request.user_hash,
        )).order_by(pastes.c.paste_id.desc()).all()

        to_mark = [p.paste_id for p in paste_list]
        db.execute(pastes.update(pastes.c.paste_id.in_(to_mark),
                                 values={'handled': True}))
        return paste_list

    @staticmethod
    def count():
        s = db.select([db.func.count(pastes.c.paste_id)])
        return db.execute(s).fetchone()[0]

    @staticmethod
    def resolve_root(paste_id):
        pastes = db.query(Paste)
        while True:
            paste = pastes.filter(Paste.c.paste_id == paste_id).first()
            if paste is None:
                return
            if paste.parent_id is None:
                return paste
            paste_id = paste.parent_id


db.mapper(Paste, pastes, properties={
    'children': db.relation(Paste,
        primaryjoin=pastes.c.parent_id==pastes.c.paste_id,
        cascade='all',
        backref=db.backref('parent', remote_side=[pastes.c.paste_id])
    )
})
