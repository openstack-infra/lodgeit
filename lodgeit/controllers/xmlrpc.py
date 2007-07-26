# -*- coding: utf-8 -*-
"""
    lodgeit.controllers.xmlrpc
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    The XMLRPC controller

    :copyright: 2007 by Armin Ronacher, Georg Brandl.
    :license: BSD
"""
import sqlalchemy as meta

from lodgeit.application import render_template
from lodgeit.controllers import BaseController
from lodgeit.database import Paste
from lodgeit.lib.xmlrpc import xmlrpc, exported
from lodgeit.lib.highlighting import STYLES, LANGUAGES, get_style, \
    get_language_for


class XmlRpcController(BaseController):

    def handle_request(self):
        if self.request.method == 'POST':
            return xmlrpc.handle_request(self.request)
        return render_template(self.request, 'xmlrpc.html')


@exported('pastes.newPaste')
def pastes_new_paste(request, language, code, parent_id=None,
                     filename='', mimetype=''):
    """
    Create a new paste. Return the new ID.

    `language` can be None, in which case the language will be
    guessed from `filename` and/or `mimetype`.
    """
    if not language:
        language = get_language_for(filename or '', mimetype or '')
    paste = Paste(code, language, parent_id)
    request.dbsession.save(paste)
    request.dbsession.flush()
    return paste.paste_id


@exported('pastes.getPaste')
def pastes_get_paste(request, paste_id):
    """
    Get all known information about a paste by a given paste id.

    Return a dictionary with these keys:
    `paste_id`, `code`, `parsed_code`, `pub_date`, `language`,
    `parent_id`, `url`.
    """
    paste = request.dbsession.query(Paste).selectfirst(Paste.c.paste_id ==
                                                       paste_id)
    if paste is None:
        return False
    return paste.to_xmlrpc_dict()


@exported('pastes.getDiff')
def pastes_get_diff(request, old_id, new_id):
    """
    Compare the two pastes and return an unified diff.
    """
    paste = request.dbsession.query(Paste)
    old = pastes.selectfirst(Paste.c.paste_id == old_id)
    new = pastes.selectfirst(Paste.c.paste_id == new_id)
    if old is None or new is None:
        return False
    return old.compare_to(new)


@exported('pastes.getRecent')
def pastes_get_recent(request, amount=5):
    """
    Return information dict (see `getPaste`) about the last `amount` pastes.
    """
    amount = min(amount, 20)
    return [x.to_xmlrpc_dict() for x in
            request.dbsession.query(Paste).select(
        order_by=[meta.desc(Paste.c.pub_date)],
        limit=amount
    )]


@exported('pastes.getLast')
def pastes_get_last(request):
    """
    Get information dict (see `getPaste`) for the most recent paste.
    """
    rv = pastes_get_recent(request, 1)
    if rv:
        return rv[0]
    return {}


@exported('pastes.getLanguages')
def pastes_get_languages(request):
    """
    Get a list of supported languages.
    """
    return LANGUAGES.items()


@exported('styles.getStyles')
def styles_get_styles(request):
    """
    Get a list of supported styles.
    """
    return STYLES.items()


@exported('styles.getStylesheet')
def styles_get_stylesheet(request, name):
    """
    Return the stylesheet for a given style.
    """
    return get_style(name)


controller = XmlRpcController
