# -*- coding: utf-8 -*-
"""
    lodgeit.controllers.static
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Static stuff.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
from lodgeit.application import render_template, PageNotFound
from lodgeit.controllers import BaseController
from lodgeit.lib.xmlrpc import xmlrpc


HELP_PAGES = [
    ('pasting',         'Pasting'),
    ('advanced',        'Advanced Features'),
    ('xmlrpc',          'Using the XMLRPC Interface'),
    ('integration',     'Scripts and Editor Integration')
]

known_help_pages = set(x[0] for x in HELP_PAGES)


class StaticController(BaseController):

    def not_found(self):
        return render_template(self.request, 'not_found.html')

    def about(self):
        return render_template(self.request, 'about.html')

    def help(self, topic=None):
        if topic is None:
            tmpl_name = 'help/index.html'
        elif topic in known_help_pages:
            tmpl_name = 'help/%s.html' % topic
        else:
            raise PageNotFound()
        return render_template(self.request, tmpl_name,
                               help_topics=HELP_PAGES,
                               current_topic=topic,
                               xmlrpc_url='http://%s/xmlrpc/' %
                                    self.request.environ['SERVER_NAME'],
                               xmlrpc_methods=xmlrpc.get_public_methods())


controller = StaticController
