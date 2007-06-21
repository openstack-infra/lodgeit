# -*- coding: utf-8 -*-
"""
    lodgeit._magic
    ~~~~~~~~~~~~~~

    Psssst. (actually this module exists because lodgeit was designed with
    the old werkzeug routing system and i was to lazy to update this)

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
import urlparse
import re


__all__ = ['Map', 'root', 'Var', 'Int', 'Bool']


class Partial(object):

    def __init__(self, builder, trace):
        self.trace = trace
        self.builder = builder

    def __div__(self, other):
        self.trace += ['/', other]
        return Partial(self.builder, self.trace)

    def __add__(self, other):
        self.trace.append(other)
        return Partial(self.builder, self.trace)

    def __sub__(self, other):
        self.trace += ['-', other]
        return Partial(self.builder, self.trace, other)

    def __gt__(self, controller):
        return Route(self.builder, self.trace, controller)


class Var(object):

    def __init__(self, name):
        self.name = name

    def get_regex(self):
        return '[^/]+'

    def to_python(self, value):
        return value

    def to_unicode(self, value):
        return unicode(value)


class Int(Var):

    def get_regex(self):
        return '\d+'

    def to_python(self, value):
        return int(value)

    def to_unicode(self, value):
        return unicode(value)


class Bool(Var):

    def get_regex(self):
        return 'yes|no'

    def to_python(self, value):
        return value == 'yes'

    def to_unicode(self, value):
        return value and 'yes' or 'no'


class Builder(object):

    def __gt__(self, controller):
        return Route(self, [], controller)

    def __div__(self, other):
        return Partial(self, [other])

    def finish(self, rule):
        pass


class AssignmentBuilder(Builder):

    def __init__(self, map):
        self.map = map

    def finish(self, route):
        self.map.add_route(route)


class Route(object):

    def __init__(self, builder, trace, controller):
        self.builder = builder
        self.controller = controller
        self.converters = {}
        self.arguments = set()
        self._bits = []

        tmp = []
        for item in trace:
            if isinstance(item, Var):
                tmp.append('(?P<%s>%s)' % (
                    item.name,
                    item.get_regex()
                ))
                self.converters[item.name] = item
                self._bits.append((True, item.name))
                self.arguments.add(item.name)
            else:
                item = unicode(item)
                tmp.append(re.escape(item))
                self._bits.append((False, item))

        self.regex = re.compile('^%s/?$(?u)' % u''.join(tmp))
        self.builder.finish(self)

    def test(self, path):
        m = self.regex.search(path)
        if m is not None:
            result = {}
            for name, value in m.groupdict().iteritems():
                result[str(name)] = self.converters[name].to_python(value)
            return result

    def build(self, values):
        tmp = []
        for is_dynamic, data in self._bits:
            if is_dynamic:
                tmp.append(self.converters[data].to_unicode(values[data]))
            else:
                tmp.append(data)
        return u''.join(tmp)


class Map(object):
    """
    URL Mapping.
    """

    def __init__(self, *routes):
        self.routes = []
        for route in routes:
            self.add_route(route)

    def add_route(self, route):
        if isinstance(route, Route):
            self.routes.append(route)
        elif isinstance(route, Partial):
            self.routes.append(route > None)
        else:
            raise TypeError('invalid route %r' % route.__class__.__name__)

    def test(self, path):
        path = path.lstrip('/')
        for route in self.routes:
            rv = route.test(path)
            if rv is not None:
                return route.controller, rv

    def build(self, environ, controller, values):
        valueset = set(values.keys())
        for route in self.routes:
            if route.controller == controller and \
               route.arguments.issubset(valueset):
                relative_url = route.build(values)
                script_name = environ.get('SCRIPT_NAME') or '/'
                if not script_name.endswith('/'):
                    script_name += '/'
                return unicode(urlparse.urljoin(script_name, relative_url))
        raise TypeError('no matching url found')


root = Builder()


def automap(f):
    """
    Decorator for fany url maps.
    """
    builder = AssignmentBuilder(Map())
    (type(f)(f.func_code, {
        'root':     builder,
        'int':      Int,
        'str':      Var,
        'bool':     Bool
    }))()
    return builder.map
