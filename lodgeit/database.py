# -*- coding: utf-8 -*-
"""
    lodgeit.database
    ~~~~~~~~~~~~~~~~

    Database fun :)

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
import time
import difflib
import sqlalchemy as meta
from cgi import escape
from random import random
from hashlib import sha1
from datetime import datetime

from lodgeit.lib.highlighting import highlight, LANGUAGES

metadata = meta.MetaData()


pastes = meta.Table('pastes', metadata,
    meta.Column('paste_id', meta.Integer, primary_key=True),
    meta.Column('code', meta.Unicode),
    meta.Column('parsed_code', meta.Unicode),
    meta.Column('parent_id', meta.Integer, meta.ForeignKey('pastes.paste_id'),
                nullable=True),
    meta.Column('pub_date', meta.DateTime),
    meta.Column('language', meta.Unicode(30)),
    meta.Column('user_hash', meta.Unicode(40), nullable=True),
    meta.Column('handled', meta.Boolean, nullable=False)
)


spam_rules = meta.Table('spam_rules', metadata,
    meta.Column('rule_id', meta.Integer, primary_key=True),
    meta.Column('rule', meta.Unicode)
)


spamsync_sources = meta.Table('spamsync_sources', metadata,
    meta.Column('source_id', meta.Integer, primary_key=True),
    meta.Column('url', meta.Unicode),
    meta.Column('last_update', meta.DateTime)
)


def generate_user_hash():
    return sha1('%s|%s' % (random(), time.time())).hexdigest()


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
    def fetch_replies(req):
        """
        Get the new replies for the owern of a request and flag them
        as handled.
        """
        s = meta.select([pastes.c.paste_id],
            pastes.c.user_hash == req.user_hash
        )
        paste_list = req.dbsession.query(Paste).select(
            (Paste.c.parent_id.in_(s)) &
            (Paste.c.handled == False) &
            (Paste.c.user_hash != req.user_hash),
            order_by=[meta.desc(Paste.c.pub_date)]
        )
        to_mark = [p.paste_id for p in paste_list]
        req.engine.execute(pastes.update(pastes.c.paste_id.in_(*to_mark)),
            handled=True
        )
        return paste_list

    @staticmethod
    def count(con):
        s = meta.select([meta.func.count(pastes.c.paste_id)])
        return con.execute(s).fetchone()[0]

    @staticmethod
    def resolve_root(sess, paste_id):
        q = sess.query(Paste)
        while True:
            paste = q.selectfirst(Paste.c.paste_id == paste_id)
            if paste is None:
                return
            if paste.parent_id is None:
                return paste
            paste_id = paste.parent_id


meta.mapper(Paste, pastes, properties={
    'children': meta.relation(Paste,
        primaryjoin=pastes.c.parent_id==pastes.c.paste_id,
        cascade='all',
        backref=meta.backref('parent', remote_side=[pastes.c.paste_id])
    )
})
