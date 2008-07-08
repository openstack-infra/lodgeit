# -*- coding: utf-8 -*-
"""
    lodgeit.lib.highlighting
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Highlighting helpers.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
from lodgeit.i18n import _
import pygments
from pygments.util import ClassNotFound
from pygments.lexers import get_lexer_by_name
from pygments.lexers import get_lexer_for_filename, get_lexer_for_mimetype
from pygments.styles import get_all_styles
from pygments.formatters import HtmlFormatter


#: we use a hardcoded list here because we want to keep the interface
#: simple
LANGUAGES = {
    'text':             _('Text'),
    'python':           _('Python'),
    'pycon':            _('Python Console Sessions'),
    'pytb':             _('Python Tracebacks'),
    'html+php':         _('PHP'),
    'html+django':      _('Django / Jinja Templates'),
    'html+mako':        _('Mako Templates'),
    'html+myghty':      _('Myghty Templates'),
    'apache':           _('Apache Config (.htaccess)'),
    'bash':             _('Bash'),
    'bat':              _('Batch (.bat)'),
    'c':                _('C'),
    'cpp':              _('C++'),
    'csharp':           _('C#'),
    'css':              _('CSS'),
    'd':                _('D'),
    'minid':            _('MiniD'),
    'smarty':           _('Smarty'),
    'html':             _('HTML'),
    'html+php':         _('PHP'),
    'html+genshi':      _('Genshi Templates'),
    'js':               _('JavaScript'),
    'java':             _('Java'),
    'jsp':              _('JSP'),
    'lua':              _('Lua'),
    'haskell':          _('Haskell'),
    'scheme':           _('Scheme'),
    'ruby':             _('Ruby'),
    'irb':              _('Interactive Ruby'),
    'perl':             _('Perl'),
    'rhtml':            _('eRuby / rhtml'),
    'tex':              _('TeX / LaTeX'),
    'xml':              _('XML'),
    'rst':              _('reStructuredText'),
    'irc':              _('IRC Logs'),
    'diff':             _('Unified Diff'),
    'vim':              _('Vim Scripts'),
    'ocaml':            _('OCaml'),
    'sql':              _('SQL'),
    'squidconf':        _('SquidConf'),
    'sourceslist':      _('sources.list'),
    'erlang':           _('Erlang'),
    'vim':              _('Vim'),
    'dylan':            _('Dylan'),
    'gas':              _('GAS')
}

STYLES = dict((x, x.title()) for x in get_all_styles())

DEFAULT_STYLE = 'friendly'


def highlight(code, language):
    """Highlight a given code to HTML"""
    lexer = get_lexer_by_name(language)
    formatter = HtmlFormatter(linenos=True, cssclass='syntax', style='pastie')
    return pygments.highlight(code, lexer, formatter)


def get_style(request):
    """Style for a given request"""
    if isinstance(request, basestring):
        style_name = request
    else:
        style_name = request.cookies.get('style')
        if style_name:
            style_name = style_name
        else:
            style_name = DEFAULT_STYLE
    try:
        f = HtmlFormatter(style=style_name)
    except ClassNotFound:
        return style_name, ''
    return style_name, f.get_style_defs(('#paste', '.syntax'))


def get_language_for(filename, mimetype):
    """Get language for filename and mimetype"""
    # XXX: this instantiates a lexer just to get at its aliases
    try:
        lexer = get_lexer_for_mimetype(mimetype)
    except ClassNotFound:
        try:
            lexer = get_lexer_for_filename(filename)
        except ClassNotFound:
            return 'text'
    for alias in lexer.aliases:
        if alias in LANGUAGES:
            return alias
    return 'text'
