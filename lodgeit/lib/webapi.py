# -*- coding: utf-8 -*-
"""
    lodgeit.lib.webapi
    ~~~~~~~~~~~~~~~~~~

    This module implements the web api.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
import inspect
from lodgeit.models import Paste
from lodgeit.database import db
from lodgeit.lib.xmlrpc import XMLRPCRequestHandler
from lodgeit.lib.json import JSONRequestHandler
from lodgeit.lib.highlighting import STYLES, LANGUAGES, get_style, \
     get_language_for


xmlrpc = XMLRPCRequestHandler()
json = JSONRequestHandler()


def exported(name, hidden=False):
    """Make a function external available via xmlrpc."""
    def proxy(f):
        xmlrpc.register_function(f, name)
        json.register_function(f, name)
        f.hidden = hidden
        return f
    return proxy


_public_methods = None
def get_public_methods():
    """Returns the public methods."""
    global _public_methods
    if _public_methods is None:
        result = []
        for name, f in json.funcs.iteritems():
            if name.startswith('system.') or f.hidden:
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
        _public_methods = result
    return _public_methods


@exported('system.listMethods')
def system_list_methods():
    return [x['name'] for x in get_public_methods()]


@exported('pastes.newPaste')
def pastes_new_paste(language, code, parent_id=None,
                     filename='', mimetype='', private=False):
    """Create a new paste. Return the new ID.

    `language` can be None, in which case the language will be
    guessed from `filename` and/or `mimetype`.
    """
    if not language:
        language = get_language_for(filename or '', mimetype or '')
    parent = None
    if parent_id:
        parent = Paste.get(parent_id)
        if parent is None:
            raise ValueError('parent paste not found')

    paste = Paste(code, language, parent, private=private)
    db.session.add(paste)
    db.session.commit()
    return paste.identifier


@exported('pastes.getPaste')
def pastes_get_paste(paste_id):
    """Get all known information about a paste by a given paste id.

    Return a dictionary with these keys:
    `paste_id`, `code`, `parsed_code`, `pub_date`, `language`,
    `parent_id`, `url`.
    """
    paste = Paste.get(paste_id)
    if paste is not None:
        return paste.to_xmlrpc_dict()


@exported('pastes.getDiff')
def pastes_get_diff(old_id, new_id):
    """Compare the two pastes and return an unified diff."""
    old = Paste.get(old_id)
    new = Paste.get(new_id)
    if old is None or new is None:
        raise ValueError('argument error, paste not found')
    return old.compare_to(new)


@exported('pastes.getRecent')
def pastes_get_recent(amount=5):
    """Return information dict (see `getPaste`) about the last
    `amount` pastes.
    """
    amount = min(amount, 20)
    return [x.to_xmlrpc_dict() for x in Paste.find_all().limit(amount)]


@exported('pastes.getLast')
def pastes_get_last():
    """Get information dict (see `getPaste`) for the most recent paste."""
    rv = pastes_get_recent(1)
    if rv:
        return rv[0]
    return {}


@exported('pastes.getLanguages')
def pastes_get_languages():
    """Get a list of supported languages."""
    # this resolves lazy translations
    return dict((key, unicode(value)) for
                key, value in LANGUAGES.iteritems())


@exported('styles.getStyles')
def styles_get_styles():
    """Get a list of supported styles."""
    return STYLES.items()


@exported('styles.getStylesheet')
def styles_get_stylesheet(name):
    """Return the stylesheet for a given style."""
    return get_style(name)
