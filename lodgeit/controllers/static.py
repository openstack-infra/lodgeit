# -*- coding: utf-8 -*-
"""
    lodgeit.controllers.static
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Static stuff.

    :copyright: 2007-2008 by Armin Ronacher, Christopher Grebs.
    :license: BSD
"""
from werkzeug.exceptions import NotFound
from lodgeit.i18n import _
from lodgeit.utils import render_template
from lodgeit.lib.xmlrpc import xmlrpc


HELP_PAGES = [
    ('pasting',         _('Pasting')),
    ('advanced',        _('Advanced Features')),
    ('xmlrpc',          _('Using the XMLRPC Interface')),
    ('integration',     _('Scripts and Editor Integration'))
]

known_help_pages = set(x[0] for x in HELP_PAGES)


class StaticController(object):

    def not_found(self):
        return render_template('not_found.html')

    def about(self):
        return render_template('about.html')

    def help(self, topic=None):
        if topic is None:
            tmpl_name = 'help/index.html'
        elif topic in known_help_pages:
            tmpl_name = 'help/%s.html' % topic
        else:
            raise NotFound()
        return render_template(
            tmpl_name,
            help_topics=HELP_PAGES,
            current_topic=topic,
            xmlrpc_url='http://%s/xmlrpc/' %
            local.request.environ['SERVER_NAME'],
            xmlrpc_methods=xmlrpc.get_public_methods()
        )


controller = StaticController
