# -*- coding: utf-8 -*-
"""
    lodgeit.controllers.xmlrpc
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    The XMLRPC controller

    :copyright: 2007-2008 by Armin Ronacher, Georg Brandl, Christopher Grebs.
    :license: BSD
"""
from lodgeit import local
from lodgeit.utils import render_template
from lodgeit.database import session, Paste
from lodgeit.lib.xmlrpc import xmlrpc, exported
from lodgeit.lib.highlighting import STYLES, LANGUAGES, get_style, \
     get_language_for


class XmlRpcController(object):

    def handle_request(self):
        if local.request.method == 'POST':
            return xmlrpc.handle_request()
        return render_template('xmlrpc.html')


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
    session.flush()
    return paste.identifier


@exported('pastes.getPaste')
def pastes_get_paste(paste_id):
    """Get all known information about a paste by a given paste id.

    Return a dictionary with these keys:
    `paste_id`, `code`, `parsed_code`, `pub_date`, `language`,
    `parent_id`, `url`.
    """
    paste = Paste.get(paste_id)
    if paste is None:
        return False
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
    return LANGUAGES.items()


@exported('styles.getStyles')
def styles_get_styles():
    """Get a list of supported styles."""
    return STYLES.items()


@exported('styles.getStylesheet')
def styles_get_stylesheet(name):
    """Return the stylesheet for a given style."""
    return get_style(name)


controller = XmlRpcController
