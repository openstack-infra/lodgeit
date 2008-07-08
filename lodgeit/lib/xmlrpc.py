# -*- coding: utf-8 -*-
"""
    lodgeit.lib.xmlrpc
    ~~~~~~~~~~~~~~~~~~

    XMLRPC helper stuff.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
import sys
import re
import inspect
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
from werkzeug import Response
from lodgeit import local


_strip_re = re.compile(r'[\x00-\x08\x0B-\x1F]')


class XMLRPCRequestHandler(SimpleXMLRPCDispatcher):

    def __init__(self):
        #: Python 2.5 requires some arguments like `allow_none`
        #: and the encoding. Python 2.4 and 2.3 doesn't.
        if sys.version_info[:2] < (2, 5):
            SimpleXMLRPCDispatcher.__init__(self)
        else:
            SimpleXMLRPCDispatcher.__init__(self, True, 'utf-8')
        self.funcs['system.listMethods'] = self.list_methods

    def list_methods(self, request):
        return [x['name'] for x in self.get_public_methods()]

    def handle_request(self):
        def dispatch(method_name, params):
            return self.funcs[method_name](*params)
        response = self._marshaled_dispatch(local.request.data, dispatch)
        return Response(response, mimetype='text/xml')

    def get_public_methods(self):
        if not hasattr(self, '_public_methods'):
            # make sure all callbacks are registered
            import lodgeit.controllers.xmlrpc
            result = []
            for name, f in self.funcs.iteritems():
                if name.startswith('system.'):
                    continue
                if f.hidden:
                    continue
                args, varargs, varkw, defaults = inspect.getargspec(f)
                if args and args[0] == 'request':
                    args = args[1:]
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


def exported(name, hidden=False):
    """Make a function external available via xmlrpc."""
    def proxy(f):
        xmlrpc.register_function(f, name)
        f.hidden = hidden
        return f
    return proxy


def strip_control_chars(s):
    return _strip_re.sub('', s or '')
