# -*- coding: utf-8 -*-
"""
    lodgeit.controllers.json
    ~~~~~~~~~~~~~~~~~~~~~~~~

    The JSON controller

    :copyright: 2008 by Armin Ronacher.
    :license: BSD
"""
from lodgeit import local
from lodgeit.lib.webapi import json
from lodgeit.utils import render_to_response


class JSONController(object):

    def handle_request(self):
        if local.request.args.get('method'):
            return json.handle_request()
        return render_to_response('json.html')


controller = JSONController
