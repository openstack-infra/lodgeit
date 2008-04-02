# -*- coding: utf-8 -*-
"""
    lodgeit.lib.highlighting
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Highlighting helpers.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
import pygments
from pygments.util import ClassNotFound
from pygments.lexers import get_lexer_by_name
from pygments.lexers import get_lexer_for_filename, get_lexer_for_mimetype
from pygments.styles import get_all_styles
from pygments.formatters import HtmlFormatter


#: we use a hardcoded list here because we want to keep the interface
#: simple
LANGUAGES = {
    'text':             'Text',
    'python':           'Python',
    'pycon':            'Python Console Sessions',
    'pytb':             'Python Tracebacks',
    'html+php':         'PHP',
    'html+django':      'Django / Jinja Templates',
    'html+mako':        'Mako Templates',
    'html+myghty':      'Myghty Templates',
    'apache':           'Apache Config (.htaccess)',
    'bash':             'Bash',
    'bat':              'Batch (.bat)',
    'c':                'C',
    'cpp':              'C++',
    'csharp':           'C#',
    'css':              'CSS',
    'd':                'D',
    'minid':            'MiniD',
    'smarty':           'Smarty',
    'html':             'HTML',
    'html+php':         'PHP',
    'html+genshi':      'Genshi Templates',
    'js':               'JavaScript',
    'java':             'Java',
    'jsp':              'JSP',
    'lua':              'Lua',
    'haskell':          'Haskell',
    'scheme':           'Scheme',
    'ruby':             'Ruby',
    'irb':              'Interactive Ruby',
    'perl':             'Perl',
    'rhtml':            'eRuby / rhtml',
    'tex':              'TeX / LaTeX',
    'xml':              'XML',
    'rst':              'reStructuredText',
    'irc':              'IRC Logs',
    'diff':             'Unified Diff',
    'vim':              'Vim Scripts',
    'ocaml':            'OCaml',
    'sql':              'SQL',
    'squidconf':        'SquidConf',
    'sourceslist':      'sources.list',
    'erlang':           'Erlang',
    'vim':              'Vim',
    'dylan':            'Dylan',
    'gas':              'GAS'
}

STYLES = dict((x, x.title()) for x in get_all_styles())

DEFAULT_STYLE = 'friendly'


def highlight(code, language, linenos):
    """
    Highlight a given code to HTML
    """
    lexer = get_lexer_by_name(language)
    formatter = HtmlFormatter(linenos=linenos, cssclass='syntax', style='pastie')
    return pygments.highlight(code, lexer, formatter)


def get_style(request):
    """
    Style for a given request
    """
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
    """
    Get language for filename and mimetype
    """
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
