# -*- coding: utf-8 -*-
"""
    lodgeit.controllers.static
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Static stuff.

    :copyright: 2007-2008 by Armin Ronacher, Christopher Grebs.
    :license: BSD
"""
from werkzeug.exceptions import NotFound
from lodgeit import local
from lodgeit.i18n import lazy_gettext
from lodgeit.utils import render_to_response
from lodgeit.lib.webapi import get_public_methods
from lodgeit.lib.highlighting import LANGUAGES


HELP_PAGES = [
    ('pasting',         lazy_gettext('Pasting')),
    ('advanced',        lazy_gettext('Advanced Features')),
    ('api',             lazy_gettext('Using the LodgeIt API')),
    ('integration',     lazy_gettext('Scripts and Editor Integration'))
]

known_help_pages = set(x[0] for x in HELP_PAGES)


class StaticController(object):

    def not_found(self):
        return render_to_response('not_found.html')

    def about(self):
        return render_to_response('about.html')

    def help(self, topic=None):
        if topic is None:
            tmpl_name = 'help/index.html'
        elif topic in known_help_pages:
            tmpl_name = 'help/%s.html' % topic
        else:
            raise NotFound()
        return render_to_response(
            tmpl_name,
            help_topics=HELP_PAGES,
            current_topic=topic,
            pastebin_url=local.request.host_url,
            formatters=LANGUAGES,
            xmlrpc_methods=get_public_methods()
        )


controller = StaticController
