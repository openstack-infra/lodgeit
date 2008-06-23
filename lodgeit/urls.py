# -*- coding: utf-8 -*-
"""
    lodgeit.urls
    ~~~~~~~~~~~~

    The URL mapping.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
from werkzeug.routing import Map, Rule

urlmap = Map([
    # paste interface
    Rule('/', endpoint='pastes/new_paste'),
    Rule('/show/<int:paste_id>/', endpoint='pastes/show_paste'),
    Rule('/raw/<int:paste_id>/', endpoint='pastes/raw_paste'),
    Rule('/compare/', endpoint='pastes/compare_paste'),
    Rule('/compare/<int:new_id>/<int:old_id>/', endpoint='pastes/compare_paste'),
    Rule('/unidiff/<int:new_id>/<int:old_id>/', endpoint='pastes/unidiff_paste'),
    Rule('/tree/<int:paste_id>/', endpoint='pastes/show_tree'),

    # captcha for new paste
    Rule('/_captcha.png', endpoint='pastes/show_captcha'),

    # paste list
    Rule('/all/', endpoint='pastes/show_all'),
    Rule('/all/<int:page>/', endpoint='pastes/show_all'),

    # xmlrpc
    Rule('/xmlrpc/', endpoint='xmlrpc/handle_request'),

    # static pages
    Rule('/about/', endpoint='static/about'),
    Rule('/help/', endpoint='static/help'),
    Rule('/help/<topic>/', endpoint='static/help'),

    # colorscheme
    Rule('/colorscheme/', endpoint='pastes/set_colorscheme'),
])
