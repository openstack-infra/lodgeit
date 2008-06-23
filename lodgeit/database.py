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
from cgi import escape
from datetime import datetime

from sqlalchemy import MetaData, Integer, Text, DateTime, ForeignKey, \
     String, Boolean, Table, Column, select, and_, func
from sqlalchemy.orm import create_session, mapper, backref, relation
from sqlalchemy.orm.scoping import ScopedSession
from werkzeug import cached_property

from lodgeit.utils import _local_manager, ctx
from lodgeit.lib.highlighting import highlight, LANGUAGES


session = ScopedSession(lambda: create_session(bind=ctx.application.engine),
                        scopefunc=_local_manager.get_ident)
metadata = MetaData()

pastes = Table('pastes', metadata,
    Column('paste_id', Integer, primary_key=True),
    Column('code', Text),
    Column('parent_id', Integer, ForeignKey('pastes.paste_id'),
             nullable=True),
    Column('pub_date', DateTime),
    Column('language', String(30)),
    Column('user_hash', String(40), nullable=True),
    Column('handled', Boolean, nullable=False)
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

    @cached_property
    def parsed_code(self):
        return highlight(self.code, self.language)

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
        """Get the new replies for the ower of a request and flag them
        as handled.
        """
        s = select([pastes.c.paste_id],
            Paste.user_hash == ctx.request.user_hash
        )

        paste_list = session.query(Paste).filter(and_(
            Paste.parent_id.in_(s),
            Paste.handled == False,
            Paste.user_hash != ctx.request.user_hash,
        )).order_by(pastes.c.paste_id.desc()).all()

        to_mark = [p.paste_id for p in paste_list]
        session.execute(pastes.update(pastes.c.paste_id.in_(to_mark),
                                      values={'handled': True}))
        return paste_list

    @staticmethod
    def count():
        s = select([func.count(pastes.c.paste_id)])
        return session.execute(s).fetchone()[0]

    @staticmethod
    def resolve_root(paste_id):
        pastes = session.query(Paste)
        while True:
            paste = pastes.filter(Paste.c.paste_id == paste_id).first()
            if paste is None:
                return
            if paste.parent_id is None:
                return paste
            paste_id = paste.parent_id


mapper(Paste, pastes, properties={
    'children': relation(Paste,
        primaryjoin=pastes.c.parent_id==pastes.c.paste_id,
        cascade='all',
        backref=backref('parent', remote_side=[pastes.c.paste_id])
    )
})
