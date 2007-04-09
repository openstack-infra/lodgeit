# -*- coding: utf-8 -*-
"""
    lodgeit.controllers.xmlrpc
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    The XMLRPC controller

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
import sqlalchemy as meta

from lodgeit.application import render_template
from lodgeit.controllers import BaseController
from lodgeit.database import Paste
from lodgeit.lib.xmlrpc import xmlrpc, exported
from lodgeit.lib.highlighting import STYLES, LANGUAGES, get_style


class XmlRpcController(BaseController):

    def handle_request(self):
        if self.request.method == 'POST':
            return xmlrpc.handle_request(self.request)
        return render_template(self.request, 'xmlrpc.html',
            methods=xmlrpc.get_public_methods(),
            interface_url='http://%s/xmlrpc/' %
                self.request.environ['SERVER_NAME']
        )

@exported('pastes.newPaste')
def pastes_new_paste(request, language, code, parent_id=None):
    """Create a new paste."""
    paste = Paste(code, language, parent_id)
    request.dbsession.save(paste)
    request.dbsession.flush()
    return {
        'paste_id':     paste.paste_id,
        'url':          paste.url
    }


@exported('pastes.getPaste')
def pastes_get_paste(request, paste_id):
    """Get all known information about a paste by a given paste id."""
    paste = request.dbsession.query(Paste).selectfirst(Paste.c.paste_id ==
                                                       paste_id)
    if paste is None:
        return False
    return paste.to_dict()


@exported('pastes.getRecent')
def pastes_get_recent(request, amount=5):
    """Return the last amount pastes."""
    amount = min(amount, 20)
    return [x.to_dict() for x in
            request.dbsession.query(Paste).select(
        order_by=[meta.desc(Paste.c.pub_date)],
        limit=amount
    )]


@exported('pastes.getLast')
def pastes_get_last(request):
    """Get the most recent paste."""
    rv = pastes_get_recent(request, 1)
    if rv:
        return rv[0]
    return {}


@exported('pastes.getLanguages')
def pastes_get_languages(request):
    """Get a list of supported languages."""
    return LANGUAGES.items()


@exported('styles.getStyles')
def styles_get_styles(request):
    """Get a list of supported styles."""
    return STYLES.items()


@exported('styles.getStylesheet')
def styles_get_stylesheet(request, name):
    """Return the stylesheet for a given style."""
    return get_style(name)


controller = XmlRpcController
