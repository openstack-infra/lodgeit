# -*- coding: utf-8 -*-
"""
    lodgeit.application
    ~~~~~~~~~~~~~~~~~~~

    the WSGI application

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
import os
import sqlalchemy
from datetime import datetime, timedelta
from werkzeug.wrappers import BaseRequest, BaseResponse
from werkzeug.utils import SharedDataMiddleware
from werkzeug.routing import NotFound, RequestRedirect
from jinja import Environment, PackageLoader

from lodgeit.urls import urlmap
from lodgeit.controllers import get_controller
from lodgeit.database import metadata, generate_user_hash, Paste
from lodgeit.lib.antispam import AntiSpam


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


def render_template(req, template_name, **context):
    """
    Render a template to a response. This automatically fetches
    the list of new replies for the layout template. It also
    adds the current request to the context. This is used for the
    welcome message.
    """
    if req.method == 'GET':
        context['new_replies'] = Paste.fetch_replies(req)
    context['request'] = req
    t = jinja_environment.get_template(template_name)
    return Response(t.render(context), mimetype='text/html; charset=utf-8')


def redirect(url, code=302):
    """
    Redirect to somewhere. Returns a nice response object.
    """
    return Response('Page Moved to %s' % url,
                    headers=[('Location', url),
                             ('Content-Type', 'text/plain')],
                    status=code)


class Request(BaseRequest):
    """
    Subclass of the `BaseRequest` object. automatically creates a new
    `user_hash` and sets `first_visit` to `True` if it's a new user.
    It also stores the engine and dbsession on it.
    """
    charset = 'utf-8'

    def __init__(self, environ, app):
        self.app = app
        self.engine = app.engine
        self.dbsession = sqlalchemy.create_session(app.engine)
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


class LodgeIt(object):
    """
    The WSGI Application
    """

    def __init__(self, dburi):
        #: name of the error handler
        self.not_found = ('static/not_found', {})
        self.engine = sqlalchemy.create_engine(dburi)
        #: make sure all tables exist.
        metadata.create_all(self.engine)
        #: create a new antispam instance
        self.antispam = AntiSpam(self)

    def __call__(self, environ, start_response):
        """
        Minimal WSGI application for request dispatching.
        """
        req = Request(environ, self)
        urls = urlmap.bind_to_environ(environ)
        try:
            endpoint, args = urls.match(req.path)
            handler = get_controller(endpoint, req)
            resp = handler(**args)
        except NotFound:
            handler = get_controller(self.not_found[0], req)
            resp = handler(**self.not_found[1])
        except RequestRedirect, err:
            resp = redirect(err.new_url)
        else:
            if req.first_visit:
                resp.set_cookie('user_hash', req.user_hash,
                    expires=datetime.utcnow() + timedelta(days=31)
                )
        # call the response as WSGI app
        return resp(environ, start_response)


def make_app(dburi):
    """
    Apply the used middlewares and create the application.
    """
    static_path = os.path.join(os.path.dirname(__file__), 'static')
    app = LodgeIt(dburi)
    app = SharedDataMiddleware(app, {
        '/static':      static_path
    })
    return app
