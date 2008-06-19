# -*- coding: utf-8 -*-
"""
    lodgeit.utils
    ~~~~~~~~~~~~~

    Serveral utilities used by LodgeIt.

    :copyright: 2007 by Christopher Grebs.
    :license: BSD
"""
import time
try:
    from hashlib import sha1
except:
    from sha import new as sha1
from random import random
from types import ModuleType
from werkzeug import Local, LocalManager, LocalProxy, BaseRequest, \
    BaseResponse
from werkzeug.routing import NotFound, RequestRedirect

from jinja2 import Environment, PackageLoader


#: context locals
_local = Local()
_local_manager = LocalManager([_local])

#: fake module type for easy access to context locals
ctx = ModuleType('ctx')
ctx.__doc__ = 'Module that holds all context locals'

#: some variables for direct access to the context locals
ctx.application = LocalProxy(_local, 'application')
ctx.request = LocalProxy(_local, 'request')

#: jinja environment for all the templates
jinja_environment = Environment(loader=PackageLoader('lodgeit', 'views',
    use_memcache=False,
    auto_reload=False
))

def datetimeformat():
    """
    Helper filter for the template
    """
    def wrapped(env, ctx, value):
        return value.strftime('%Y-%m-%d %H:%M')
    return wrapped

jinja_environment.filters['datetimeformat'] = datetimeformat


def generate_user_hash():
    return sha1('%s|%s' % (random(), time.time())).hexdigest()


class Request(BaseRequest):
    """
    Subclass of the `BaseRequest` object. automatically creates a new
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


class Response(BaseResponse):
    """
    Subclass the response object for later extension.
    """
    charset = 'utf-8'


class PageNotFound(NotFound):
    """
    Internal exception used to tell the application to show the
    error page.
    """


def render_template(template_name, **tcontext):
    """
    Render a template to a response. This automatically fetches
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


def redirect(url, code=302):
    """
    Redirect to somewhere. Returns a nice response object.
    """
    return Response('Page Moved to %s' % url,
                    headers=[('Location', url),
                             ('Content-Type', 'text/plain')],
                    status=code)
