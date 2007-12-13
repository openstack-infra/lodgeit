# -*- coding: utf-8 -*-
"""
    lodgeit.controllers.xmlrpc
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    The XMLRPC controller

    :copyright: 2007 by Armin Ronacher, Georg Brandl.
    :license: BSD
"""
from lodgeit.utils import ctx, render_template
from lodgeit.controllers import BaseController
from lodgeit.database import db, Paste
from lodgeit.lib.xmlrpc import xmlrpc, exported
from lodgeit.lib.highlighting import STYLES, LANGUAGES, get_style, \
    get_language_for


class XmlRpcController(BaseController):

    def handle_request(self):
        if ctx.request.method == 'POST':
            return xmlrpc.handle_request()
        return render_template('xmlrpc.html')


@exported('pastes.newPaste')
def pastes_new_paste(language, code, parent_id=None,
                     filename='', mimetype=''):
    """
    Create a new paste. Return the new ID.

    `language` can be None, in which case the language will be
    guessed from `filename` and/or `mimetype`.
    """
    if not language:
        language = get_language_for(filename or '', mimetype or '')
    paste = Paste(code, language, parent_id)
    db.session.save(paste)
    db.session.flush()
    return paste.paste_id


@exported('pastes.getPaste')
def pastes_get_paste(paste_id):
    """
    Get all known information about a paste by a given paste id.

    Return a dictionary with these keys:
    `paste_id`, `code`, `parsed_code`, `pub_date`, `language`,
    `parent_id`, `url`.
    """
    paste = db.session.query(Paste).filter(Paste.c.paste_id ==
                                          paste_id).first()
    if paste is None:
        return False
    return paste.to_xmlrpc_dict()


@exported('pastes.getDiff')
def pastes_get_diff(old_id, new_id):
    """
    Compare the two pastes and return an unified diff.
    """
    pastes = db.session.query(Paste)
    old = pastes.filter(Paste.c.paste_id == old_id).first()
    new = pastes.filter(Paste.c.paste_id == new_id).first()
    if old is None or new is None:
        return False
    return old.compare_to(new)


@exported('pastes.getRecent')
def pastes_get_recent(amount=5):
    """
    Return information dict (see `getPaste`) about the last `amount` pastes.
    """
    amount = min(amount, 20)
    return [x.to_xmlrpc_dict() for x in
            db.session.query(Paste).order_by(
                Paste.pub_date.desc()
            ).limit(amount)]


@exported('pastes.getLast')
def pastes_get_last():
    """
    Get information dict (see `getPaste`) for the most recent paste.
    """
    rv = pastes_get_recent(1)
    if rv:
        return rv[0]
    return {}


@exported('pastes.getLanguages')
def pastes_get_languages():
    """
    Get a list of supported languages.
    """
    return LANGUAGES.items()


@exported('styles.getStyles')
def styles_get_styles():
    """
    Get a list of supported styles.
    """
    return STYLES.items()


@exported('styles.getStylesheet')
def styles_get_stylesheet(name):
    """
    Return the stylesheet for a given style.
    """
    return get_style(name)


@exported('antispam.addRule', hidden=True)
def antispam_add_rule(rule):
    ctx.application.antispam.add_rule(rule)


@exported('antispam.removeRule', hidden=True)
def antispam_remove_rule(rule):
    ctx.application.antispam.remove_rule(rule)


@exported('antispam.getRules', hidden=True)
def antispam_get_rules():
    return sorted(ctx.application.antispam.get_rules())


@exported('antispam.hasRule', hidden=True)
def antispam_has_rule(rule):
    return ctx.application.antispam.rule_exists(rule)


@exported('antispam.addSyncSource', hidden=True)
def antispam_add_sync_source(url):
    ctx.application.antispam.add_sync_source(url)


@exported('antispam.removeSyncSource', hidden=True)
def antispam_remove_sync_source(url):
    ctx.application.antispam.remove_sync_source(url)


@exported('antispam.getSyncSources', hidden=True)
def antispam_get_sync_sources():
    return sorted(ctx.application.antispam.get_sync_sources())


@exported('antispam.hasSyncSource', hidden=True)
def antispam_has_sync_source(url):
    return url in ctx.application.antispam.get_sync_sources()


@exported('antispam.triggerSync', hidden=True)
def antispam_trigger_sync():
    ctx.application.antispam.sync_sources()


controller = XmlRpcController
