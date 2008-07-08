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
from werkzeug.exceptions import HTTPException, NotFound

from babel import Locale

from lodgeit import i18n
from lodgeit.utils import _local_manager, ctx, jinja_environment, \
     Request
from lodgeit.database import metadata, session, Paste
from lodgeit.urls import urlmap
from lodgeit.controllers import get_controller


class LodgeIt(object):
    """The WSGI Application"""

    def __init__(self, dburi, secret_key):
        #: the secret key used by the captcha
        self.secret_key = secret_key

        #: name of the error handler
        self.not_found = ('static/not_found', {})
        self.engine = sqlalchemy.create_engine(dburi, convert_unicode=True)

        #: make sure all tables exist.
        metadata.create_all(self.engine)

        #: 18n setup
        #TODO: load from user cookie
        self.locale = None
        self.set_locale('en_US')

        #: jinja_environment update
        jinja_environment.globals.update(
            i18n_languages=i18n.list_languages()
        )
        jinja_environment.filters.update(
            datetimeformat=i18n.format_datetime
        )

        #: bind the application to the current context local
        self.bind_to_context()

    def bind_to_context(self):
        ctx.application = self

    def set_locale(self, locale):
        if not self.locale or self.locale.language != locale:
            self.locale = Locale(locale)
        self.translations = i18n.load_translations(self.locale)

        #: update gettext translations
        jinja_environment.install_gettext_translations(self.translations)

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
            handler = get_controller(self.not_found[0])
            resp = handler(**self.not_found[1])
        except HTTPException, e:
            resp = e.get_response(environ)
        else:
            if request.first_visit:
                resp.set_cookie('user_hash', request.user_hash,
                    expires=datetime.utcnow() + timedelta(days=31)
                )

        return ClosingIterator(resp(environ, start_response),
                               [_local_manager.cleanup, session.remove])


def make_app(dburi, secret_key, debug=False, shell=False):
    """Apply the used middlewares and create the application."""
    static_path = os.path.join(os.path.dirname(__file__), 'static')
    app = LodgeIt(dburi, secret_key)
    if debug:
        app.engine.echo = True
    if not shell:
        # we don't need access to the shared data middleware in shell mode
        app = SharedDataMiddleware(app, {
            '/static':      static_path
        })
    return app
