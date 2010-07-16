# -*- coding: utf-8 -*-
"""
    lodgeit.lib.highlighting
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Highlighting helpers.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
import re
import pygments
import csv
from operator import itemgetter
from pygments.util import ClassNotFound
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, \
     get_lexer_for_mimetype, PhpLexer, TextLexer, get_all_lexers
from pygments.styles import get_all_styles
from pygments.formatters import HtmlFormatter

from lodgeit import local
from lodgeit.i18n import lazy_gettext as _
from lodgeit.utils import render_template
from lodgeit.lib.diff import prepare_udiff
from lodgeit.lib.compilerparser import parse_gcc_messages, \
     parse_javac_messages

from werkzeug import escape


#: we use a hardcoded list here because we want to keep the interface
#: simple
def _get_pygments_lexers(add_empty=True):
    r = []
    if add_empty:
        r.append(('', ''),)
    for lexer in get_all_lexers():
        r.append((lexer[1][0], _(lexer[0])),)
    return r

LANGUAGES = _get_pygments_lexers()
#: Add LodgeIt's special language lexers
#: Or at least ensure those exist.
LANGUAGES.extend([
    ('csv',              _('CSV')),
    ('javac-messages',   _('javac Messages')),
    ('diff',             _('Unified Diff')),
    ('gcc-messages',     _('GCC Messages')),
    ('creole',           _('Creole Wiki')),
    ('multi',            _('Multi-File')),
])
LANGUAGES = dict(sorted(LANGUAGES, key=itemgetter(1)))


STYLES = dict((x, x.title()) for x in get_all_styles())

DEFAULT_STYLE = 'friendly'

_section_marker_re = re.compile(r'^(?<!\\)###\s*(.*?)(?:\[(.+?)\])?\s*$(?m)')
_escaped_marker = re.compile(r'^\\(?=###)(?m)')


def highlight(code, language, _preview=False, _linenos=True):
    """Highlight a given code to HTML."""
    if not _preview:
        if language == 'diff':
            return highlight_diff(code)
        elif language == 'creole':
            return format_creole(code)
        elif language == 'csv':
            return format_csv(code)
        elif language == 'gcc-messages':
            return format_compiler_messages(parse_gcc_messages(code), 'gcc')
        elif language == 'javac-messages':
            return format_compiler_messages(parse_javac_messages(code), 'javac')
    if language == 'multi':
        return highlight_multifile(code)
    elif language == 'php':
        lexer = PhpLexer(startinline=True)
    else:
        try:
            lexer = get_lexer_by_name(language)
        except ClassNotFound:
            lexer = TextLexer()
    style = get_style(name_only=True)
    formatter = HtmlFormatter(linenos=_linenos, cssclass='syntax', style=style)
    return u'<div class="code">%s</div>' % \
           pygments.highlight(code, lexer, formatter)


def preview_highlight(code, language, num=5):
    """Returns a highlight preview."""
    # languages that do not support preview highlighting
    if language == 'creole' or language == 'csv':
        parsed_code = None
    else:
        parsed_code = highlight(code, language, _preview=True)
    try:
        if parsed_code is None:
            raise ValueError()
        start = parsed_code.index('</pre>')
        code = parsed_code[
            parsed_code.index('<pre>', start) + num:
            parsed_code.index('</pre>', start + 7)
        ].strip('\n').splitlines()
    except (IndexError, ValueError):
        code = code.strip('\n').splitlines()
    lines = code[:num]
    if len(code) > num:
        lines.append('...')
    code = '\n'.join(lines)
    return '<pre class="syntax">%s</pre>' % code


def highlight_diff(code, _linenos=True):
    """Highlights an unified diff."""
    diffs, info = prepare_udiff(code)
    if code and not diffs:
        # the diff was quite very much malformatted.
        # TODO: we do not yet support diffs made by GNU Diff!
        lexer = TextLexer()
        style = get_style(name_only=True)
        formatter = HtmlFormatter(linenos=_linenos, cssclass='syntax',
                                  style=style)
        return u'<div class="code">%s</div>' % \
               pygments.highlight(code, lexer, formatter)
    return render_template('utils/udiff.html', diffs=diffs, info=info,
                           linenos=_linenos)


def format_creole(code):
    """Format creole syntax."""
    from creoleparser import creole2html
    rv = creole2html(code)
    if isinstance(rv, str):
        rv = rv.decode('utf-8')
    return u'<div class="wikitext">%s</div>' % rv


def format_csv(code):
    """Display CSV code."""
    class dialect(csv.excel):
        quoting = csv.QUOTE_ALL
    result = ['<div class="csv"><table>']
    lines = code.encode('utf-8').splitlines()
    for idx, row in enumerate(csv.reader(lines, dialect=dialect)):
        result.append('<tr class="%s">' % (idx % 2 == 0 and 'even' or 'odd'))
        for col in row:
            result.append('<td>%s</td>' % escape(col))
        result.append('</tr>\n')
    result.append('</table></div>')
    return ''.join(result).decode('utf-8')


def format_compiler_messages(lines, compiler):
    """Highlights compiler messages."""
    return render_template('utils/compiler-messages.html',
                           lines=lines, compiler=compiler)


def highlight_multifile(code):
    """Multi-file highlighting."""
    result = []
    last = [0, None, 'text']

    def highlight_section(pos):
        start, filename, lang = last
        section_code = _escaped_marker.sub('', code[start:pos])
        if section_code:
            result.append(u'<div class="section">%s%s</div>' % (
                filename and u'<p class="filename">%s</p>'
                    % escape(filename) or u'',
                highlight(section_code, lang)
            ))

    for match in _section_marker_re.finditer(code):
        start = match.start()
        highlight_section(start)
        filename, lang = match.groups()
        if lang is None:
            lang = get_language_for(filename)
        else:
            lang = lookup_language_alias(lang)
        last = [match.end(), filename, lang]

    highlight_section(len(code))

    return u'<div class="multi">%s</div>' % u'\n'.join(result)


def get_style(request=None, name_only=False):
    """Style for a given request or style name."""
    request = request or local.request
    if not request:
        style_name = DEFAULT_STYLE
    elif isinstance(request, basestring):
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
        style_name = DEFAULT_STYLE
        f = HtmlFormatter(style=style_name)
    if name_only:
        return style_name
    return style_name, f.get_style_defs(('#paste', '.syntax'))


def get_language_for(filename, mimetype=None, default='text'):
    """Get language for filename and mimetype"""
    try:
        if mimetype is None:
            raise ClassNotFound()
        lexer = get_lexer_for_mimetype(mimetype)
    except ClassNotFound:
        try:
            lexer = get_lexer_for_filename(filename)
        except ClassNotFound:
            return default
    return get_known_alias(lexer, default)


def lookup_language_alias(alias, default='text'):
    """When passed a pygments alias returns the alias from LANGUAGES.  If
    the alias does not exist at all or is not in languages, `default` is
    returned.
    """
    if alias in LANGUAGES:
        return alias
    try:
        lexer = get_lexer_by_name(alias)
    except ClassNotFound:
        return default
    return get_known_alias(lexer)


def get_known_alias(lexer, default='text'):
    """Return the known alias for the lexer."""
    for alias in lexer.aliases:
        if alias in LANGUAGES:
            return alias
    return default


def list_languages():
    """List all languages."""
    languages = LANGUAGES.items()
    languages.sort(key=lambda x: x[1].lstrip(' _-.').lower())
    return languages
