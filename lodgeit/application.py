# -*- coding: utf-8 -*-
"""
    lodgeit.application
    ~~~~~~~~~~~~~~~~~~~

    the WSGI application

    :copyright: 2007 by Armin Ronacher, Christopher Grebs.
                2008 by Christopher Grebs.
    :license: BSD
"""
import os
import sqlalchemy
from datetime import datetime, timedelta
from werkzeug import SharedDataMiddleware, ClosingIterator
from lodgeit.utils import _local_manager, ctx, jinja_environment, \
    Request, generate_user_hash, NotFound, RequestRedirect, redirect
from lodgeit.database import metadata, db, Paste
from lodgeit.lib.antispam import AntiSpam
from lodgeit.urls import urlmap
from lodgeit.controllers import get_controller


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
        #: bind the application to the current context local
        self.bind_to_context()
        #: create a new AntiSpam instance
        self.antispam = AntiSpam()

    def bind_to_context(self):
        ctx.application = self

    def __call__(self, environ, start_response):
        """
        Minimal WSGI application for request dispatching.
        """
        #: bind the application to the new context local
        self.bind_to_context()
        request = Request(environ)
        request.bind_to_context()
        urls = urlmap.bind_to_environ(environ)
        try:
            endpoint, args = urls.match(request.path)
            handler = get_controller(endpoint)
            resp = handler(**args)
        except NotFound:
            handler = get_controller(self.not_found[0])
            resp = handler(**self.not_found[1])
        except RequestRedirect, err:
            resp = redirect(err.new_url)
        else:
            if request.first_visit:
                resp.set_cookie('user_hash', request.user_hash,
                    expires=datetime.utcnow() + timedelta(days=31)
                )

        return ClosingIterator(resp(environ, start_response),
                               [_local_manager.cleanup, db.session.remove])


def make_app(dburi, debug=False, shell=False):
    """
    Apply the used middlewares and create the application.
    """
    static_path = os.path.join(os.path.dirname(__file__), 'static')
    app = LodgeIt(dburi)
    if debug:
        app.engine.echo = True
    if not shell:
        # we don't need access to the shared data middleware in shell mode
        app = SharedDataMiddleware(app, {
            '/static':      static_path
        })
    return app
