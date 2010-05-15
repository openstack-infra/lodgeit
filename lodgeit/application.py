# -*- coding: utf-8 -*-
"""
    lodgeit.application
    ~~~~~~~~~~~~~~~~~~~

    the WSGI application

    :copyright: 2007-2009 by Armin Ronacher, Christopher Grebs.
    :license: BSD
"""
import os
from datetime import datetime, timedelta
from babel import Locale
from werkzeug import SharedDataMiddleware, ClosingIterator
from werkzeug.exceptions import HTTPException, NotFound
from sqlalchemy import create_engine
from lodgeit import i18n
from lodgeit.local import application, ctx, _local_manager
from lodgeit.urls import urlmap
from lodgeit.utils import COOKIE_NAME, Request, jinja_environment
from lodgeit.database import db
from lodgeit.models import Paste
from lodgeit.controllers import get_controller


class LodgeIt(object):
    """The WSGI Application"""

    def __init__(self, dburi, secret_key):
        self.secret_key = secret_key

        #: bind metadata, create engine and create all tables
        self.engine = engine = create_engine(dburi, convert_unicode=True)
        db.metadata.bind = engine
        db.metadata.create_all(engine, [Paste.__table__])

        #: jinja_environment update
        jinja_environment.globals.update({
            'i18n_languages': i18n.list_languages()})
        jinja_environment.filters.update({
            'datetimeformat': i18n.format_datetime})
        jinja_environment.install_null_translations()

        #: bind the application to the current context local
        self.bind_to_context()

        self.cleanup_callbacks = (db.session.close, _local_manager.cleanup,
                                  self.bind_to_context())

    def bind_to_context(self):
        ctx.application = application = self

    def __call__(self, environ, start_response):
        """Minimal WSGI application for request dispatching."""
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
            handler = get_controller('static/not_found')
            resp = handler()
        except HTTPException, e:
            resp = e.get_response(environ)
        else:
            expires = datetime.utcnow() + timedelta(days=31)
            if request.first_visit or request.session.should_save:
                request.session.save_cookie(resp, COOKIE_NAME,
                                            expires=expires)

        return ClosingIterator(resp(environ, start_response),
                               self.cleanup_callbacks)


def make_app(dburi, secret_key, debug=False, shell=False):
    """Apply the used middlewares and create the application."""
    static_path = os.path.join(os.path.dirname(__file__), 'static')
    app = LodgeIt(dburi, secret_key)
    if debug:
        app.engine.echo = True
    app.bind_to_context()
    if not shell:
        # we don't need access to the shared data middleware in shell mode
        app = SharedDataMiddleware(app, {
            '/static': static_path})
    return app
