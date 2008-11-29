# -*- coding: utf-8 -*-
"""
    lodgeit.lib.json
    ~~~~~~~~~~~~~~~~

    This module implements a simple JSON API.

    :copyright: 2008 by Armin Ronacher.
    :license: BSD
"""
from simplejson import dumps, loads
from werkzeug import Response
from lodgeit import local


class JSONRequestHandler(object):

    def __init__(self):
        self.funcs = {}

    def register_function(self, func, name=None):
        self.funcs[name or func.__name__] = func

    def handle_request(self):
        try:
            method_name = local.request.args['method']
            if not local.request.data:
                args = ()
                kwargs = {}
            else:
                args = loads(local.request.data)
                if isinstance(args, dict):
                    kwargs = dict((str(key), value) for
                                  key, value in args.iteritems())
                    args = ()
                elif isinstance(args, list):
                    kwargs = {}
                else:
                    raise TypeError('arguments as object or list expected')
            response = {
                'data':     self.funcs[method_name](*args, **kwargs),
                'error':    None
            }
        except Exception, e:
            response = {'data': None, 'error': str(e).decode('utf-8')}
        body = dumps(response, indent=local.request.is_xhr and 2 or 0)
        return Response(body + '\n', mimetype='application/json')
