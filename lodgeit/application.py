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
from wsgitk.wrappers import BaseRequest, BaseResponse
from wsgitk.static import StaticExports
from jinja import Environment, PackageLoader

from lodgeit.urls import urlmap
from lodgeit.controllers import get_controller
from lodgeit.database import metadata, generate_user_hash, Paste


#: jinja environment for all the templates
jinja_environment = Environment(loader=PackageLoader('lodgeit', 'views',
    use_memcache=True,
    cache_folder='/tmp',
    auto_reload=True
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
                    status=302)


class Request(BaseRequest):
    """
    Subclass of the `BaseRequest` object. automatically creates a new
    `user_hash` and sets `first_visit` to `True` if it's a new user.
    It also stores the engine and dbsession on it.
    """

    def __init__(self, environ, engine):
        self.engine = engine
        self.dbsession = sqlalchemy.create_session(engine)
        super(Request, self).__init__(environ)

        # check the user hash. an empty cookie is considered
        # begin a new session.
        self.user_hash = ''
        self.first_visit = False
        if 'user_hash' in self.cookies:
            self.user_hash = self.cookies['user_hash'].value
        if not self.user_hash:
            self.user_hash = generate_user_hash()
            self.first_visit = True


class Response(BaseResponse):
    """
    Subclass the response object for later extension.
    """


class PageNotFound(Exception):
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

    def __call__(self, environ, start_response):
        """
        Minimal WSGI application for request dispatching.
        """
        req = Request(environ, self.engine)
        rv = urlmap.test(environ.get('PATH_INFO', ''))
        try:
            if rv is None:
                raise PageNotFound()
            handler = get_controller(rv[0], req)
            response = handler(**rv[1])
        except PageNotFound:
            handler = get_controller(self.not_found[0], req)
            response = handler(**self.not_found[1])
        # on first visit we send out the cookie
        if req.first_visit:
            response.set_cookie('user_hash', req.user_hash,
                expires=datetime.utcnow() + timedelta(days=31)
            )
        # call the response as WSGI app
        return response(environ, start_response)


def make_app(dburi):
    """
    Apply the used middlewares and create the application.
    """
    static_path = os.path.join(os.path.dirname(__file__), 'static')
    app = LodgeIt(dburi)
    app = StaticExports(app, {
        '/static':      static_path
    })
    return app
