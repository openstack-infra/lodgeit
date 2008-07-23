# -*- coding: utf-8 -*-
"""
    lodgeit.utils
    ~~~~~~~~~~~~~

    Serveral utilities used by LodgeIt.

    :copyright: 2007-2008 by Christopher Grebs.
    :license: BSD
"""
import re
import time
from os import path
from random import random
from functools import partial
from werkzeug import Request as RequestBase, Response
from werkzeug.contrib.securecookie import SecureCookie
from jinja2 import Environment, FileSystemLoader
from lodgeit import local

try:
    from hashlib import sha1
except:
    from sha import new as sha1

#: Jinja2 Environment for our template handling
jinja_environment = Environment(loader=FileSystemLoader(
    path.join(path.dirname(__file__), 'views')),
    extensions=['jinja2.ext.i18n'])

#: constants
_word_only = partial(re.compile(r'[^a-zA-Z0-9]').sub, '')
COOKIE_NAME = u'lodgeit_session'


def generate_user_hash():
    """Generates an more or less unique SHA1 hash."""
    return sha1('%s|%s' % (random(), time.time())).hexdigest()


def generate_paste_hash():
    """Generates a more or less unique-truncated SHA1 hash."""
    while 1:
        digest = sha1('%s|%s' % (random(), time.time())).digest()
        val = _word_only(digest.encode('base64').strip().splitlines()[0])[:20]
        # sanity check.  number only not allowed (though unlikely)
        if not val.isdigit():
            return val


class Request(RequestBase):
    """Subclass of the `Request` object. automatically creates a new
    `user_hash` and sets `first_visit` to `True` if it's a new user.
    It also stores the engine and dbsession on it.
    """
    charset = 'utf-8'

    def __init__(self, environ):
        super(Request, self).__init__(environ)
        self.first_visit = False
        session = SecureCookie.load_cookie(self, COOKIE_NAME,
            local.application.secret_key)
        user_hash = session.get('user_hash')

        if not user_hash:
            session['user_hash'] = generate_user_hash()
            self.first_visit = True
        self.user_hash = session['user_hash']
        self.session = session

    def bind_to_context(self):
        local.request = self


def render_template(template_name, plain=False, **tcontext):
    """Render a template to a response. This automatically fetches
    the list of new replies for the layout template. It also
    adds the current request to the context. This is used for the
    welcome message.
    """
    from lodgeit.database import Paste
    if local.request.method == 'GET':
        tcontext['new_replies'] = Paste.fetch_replies()
    if local.request:
        tcontext['request'] = local.request
    if local.application:
        tcontext['active_language'] = local.application.locale.language
    t = jinja_environment.get_template(template_name)
    if not plain:
        resp = Response(t.render(tcontext), mimetype='text/html; charset=utf-8')
    else:
        resp = t.render(tcontext)
    return resp
