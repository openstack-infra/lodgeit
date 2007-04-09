# -*- coding: utf-8 -*-
"""
    lodgeit.controllers.static
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Static stuff.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
from lodgeit.application import render_template
from lodgeit.controllers import BaseController


class StaticController(BaseController):

    def not_found(self):
        return render_template(self.request, 'not_found.html')

    def about(self):
        return render_template(self.request, 'about.html')

controller = StaticController
