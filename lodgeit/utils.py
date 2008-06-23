# -*- coding: utf-8 -*-
"""
    lodgeit.utils
    ~~~~~~~~~~~~~

    Serveral utilities used by LodgeIt.

    :copyright: 2007 by Christopher Grebs.
    :license: BSD
"""
import time
from os import path
try:
    from hashlib import sha1
except:
    from sha import new as sha1
from random import random

from werkzeug import Local, LocalManager, LocalProxy, \
     Request as RequestBase, Response
from jinja2 import Environment, FileSystemLoader


#: context locals
ctx = Local()
_local_manager = LocalManager(ctx)

#: jinja environment for all the templates
jinja_environment = Environment(loader=FileSystemLoader(
    path.join(path.dirname(__file__), 'views')))


def datetimeformat(obj):
    """Helper filter for the template"""
    return obj.strftime('%Y-%m-%d %H:%M')

jinja_environment.filters['datetimeformat'] = datetimeformat


def generate_user_hash():
    """Generates an more or less unique SHA1 hash."""
    return sha1('%s|%s' % (random(), time.time())).hexdigest()


class Request(RequestBase):
    """Subclass of the `Request` object. automatically creates a new
    `user_hash` and sets `first_visit` to `True` if it's a new user.
    It also stores the engine and dbsession on it.
    """
    charset = 'utf-8'

    def __init__(self, environ):
        self.app = ctx.application
        super(Request, self).__init__(environ)

        # check the user hash. an empty cookie is considered
        # begin a new session.
        self.user_hash = ''
        self.first_visit = False
        if 'user_hash' in self.cookies:
            self.user_hash = self.cookies['user_hash']
        if not self.user_hash:
            self.user_hash = generate_user_hash()
            self.first_visit = True

    def bind_to_context(self):
        ctx.request = self


def render_template(template_name, **tcontext):
    """Render a template to a response. This automatically fetches
    the list of new replies for the layout template. It also
    adds the current request to the context. This is used for the
    welcome message.
    """
    from lodgeit.database import Paste
    if ctx.request.method == 'GET':
        tcontext['new_replies'] = Paste.fetch_replies()
    tcontext['request'] = ctx.request
    t = jinja_environment.get_template(template_name)
    return Response(t.render(tcontext), mimetype='text/html; charset=utf-8')
