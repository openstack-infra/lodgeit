# -*- coding: utf-8 -*-
"""
    lodgeit.urls
    ~~~~~~~~~~~~

    The URL mapping.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
from lodgeit._magic import automap


@automap
def urlmap():
    # paste interface
    root > 'pastes/new_paste'
    root / 'show' / int('paste_id') > 'pastes/show_paste'
    root / 'raw' / int('paste_id') > 'pastes/raw_paste'
    root / 'compare' / int('new_id') / int('old_id') > 'pastes/compare_paste'
    root / 'tree' / int('paste_id') > 'pastes/show_tree'

    # paste list
    root / 'all' > 'pastes/show_all'
    root / 'all' / int('page') > 'pastes/show_all'

    # xmlrpc
    root / 'xmlrpc' > 'xmlrpc/handle_request'

    # static pages
    root / 'about' > 'static/about'

    # redirect pages
    root / 'compare' > 'pastes/compare_paste'
    root / 'colorscheme' > 'pastes/set_colorscheme'
