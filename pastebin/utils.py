# -*- coding: utf-8 -*-
"""
    pastebin.utils
    ~~~~~~~~~~~~~~

    Lodge It pastebin utilities.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD
"""
import math
import inspect
import time
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
from difflib import HtmlDiff
from cgi import escape
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, Http404
from django.template import Context, loader
from django.conf import settings
from django.contrib.sites.models import Site
from pygments.formatters import HtmlFormatter


class TemplateResponse(HttpResponse):

    def get_globals(self, request):
        from pastebin.pastes.models import STYLES, Paste, Tag
        styles = []
        current_style = request.session.get('style') or 'pastie'
        style = None
        for key, value in STYLES:
            if style is None and key == current_style:
                style = HtmlFormatter(style=key)
            styles.append({
                'value':        key,
                'caption':      value,
                'selected':     key == current_style
            })
        return {
            'SETTINGS':     settings,
            'STYLES':       styles,
            'STYLE':        style.get_style_defs('.syntax'),
            'RECENT':       Paste.objects.order_by('-pub_date') \
                                         .filter(private=False)[:5],
            'TAGS':         Tag.objects.get_popular()
        }

    def __init__(self, request, template_name, context={}, mimetype=None):
        t = loader.get_template(template_name)
        context.update(self.get_globals(request))
        response = t.render(Context(context))
        HttpResponse.__init__(self, response, mimetype)


def templated(template_name):
    def decorator(f):
        def proxy(*args, **kwargs):
            request = args[0]
            try:
                rv = f(*args, **kwargs)
            except ObjectDoesNotExist:
                raise Http404()
            if isinstance(rv, HttpResponse):
                return rv
            return TemplateResponse(request, template_name, rv)
        return proxy
    return decorator


class SaneHtmlDiff(HtmlDiff):
    _table_template = '''%(data_rows)s'''

    def _format_line(self, side, flag, linenum, text):
        try:
            linenum = '%d' % linenum
        except:
            pass
        return ('<td class="diff_header">%s</td>'
                '<td class="diff_data">%s</td>') % (
            linenum, escape(text)
        )


def render_diff(source1, source2):
    lines1 = source1.splitlines()
    lines2 = source2.splitlines()
    d = SaneHtmlDiff()
    return d.make_table(lines1, lines2)


class Pagination(object):

    def __init__(self, query, page, link, per_page=10):
        self.query = query
        self.page = int(page)
        self.link = link
        self.per_page = per_page

    def get_objects(self):
        idx = (self.page - 1) * self.per_page
        result = self.query[idx:idx + self.per_page]
        if self.page != 1 and not result:
            raise Http404()
        return result

    def generate(self, normal='<a href="%(href)s">%(page)d</a>',
                 active='<strong>%(page)d</strong>',
                 commata=',\n',
                 ellipsis=' ...\n',
                 threshold=3):
        was_ellipsis = False
        result = []
        total = self.query.count()
        pages = int(math.ceil(total / float(self.per_page)))
        for num in xrange(1, pages + 1):
            if num <= threshold or num > pages - threshold or \
               abs(self.page - num) < math.ceil(threshold / 2.0):
                if result and result[-1] != ellipsis:
                    result.append(commata)
                was_space = False
                if num == 0:
                    link = self.link
                else:
                    link = '%s%d/' % (self.link, num)
                if num == self.page:
                    template = active
                else:
                    template = normal
                result.append(template % {
                    'href':     link,
                    'page':     num
                })
            elif not was_ellipsis:
                was_ellipsis = True
                result.append(ellipsis)
        return ''.join(result)


class XMLRPCRequestHandler(SimpleXMLRPCDispatcher):
    
    def handle_request(self, request):
        response = self._marshaled_dispatch(request.raw_post_data)
        return HttpResponse(response, mimetype='text/xml')

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


def external(name):
    """Make a function external available via xmlrpc."""
    def proxy(f):
        xmlrpc.register_function(f, name)
        return f
    return proxy


def get_timestamp(d):
    """Return the UNIX timestamp of a datetime object"""
    return int(time.mktime(d.timetuple()) + d.microsecond / 1e6)


def get_external_url(obj):
    """Return the external url to an object."""
    return 'http://%s%s' % (
        Site.objects.get_current().domain,
        obj.get_absolute_url()
    )
