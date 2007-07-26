# -*- coding: utf-8 -*-
"""
    lodgeit.lib.xmlrpc
    ~~~~~~~~~~~~~~~~~~

    XMLRPC helper stuff.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
import re
import inspect
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher

from lodgeit.application import Response

_strip_re = re.compile(r'[\x00-\x08\x0B-\x1F]')


class XMLRPCRequestHandler(SimpleXMLRPCDispatcher):

    def __init__(self):
        SimpleXMLRPCDispatcher.__init__(self, True, 'utf-8')

    def handle_request(self, request):
        def dispatch(method_name, params):
            method = self.funcs[method_name]
            if method_name.startswith('system.'):
                return method(*params)
            return method(request, *params)
        response = self._marshaled_dispatch(request.data, dispatch)
        return Response(response, mimetype='text/xml')

    def get_public_methods(self):
        if not hasattr(self, '_public_methods'):
            result = []
            for name, f in self.funcs.iteritems():
                if name.startswith('system.'):
                    continue
                args, varargs, varkw, defaults = inspect.getargspec(f)
                result.append({
                    'name':         name,
                    'doc':          inspect.getdoc(f) or '',
                    'signature':    inspect.formatargspec(
                        args, varargs, varkw, defaults,
                        formatvalue=lambda o: '=' + repr(o)
                    )
                })
            result.sort(key=lambda x: x['name'].lower())
            self._public_methods = result
        return self._public_methods


xmlrpc = XMLRPCRequestHandler()
xmlrpc.register_introspection_functions()


def exported(name):
    """Make a function external available via xmlrpc."""
    def proxy(f):
        xmlrpc.register_function(f, name)
        return f
    return proxy


def strip_control_chars(s):
    return _strip_re.sub('', s)
