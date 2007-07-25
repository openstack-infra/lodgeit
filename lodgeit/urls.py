# -*- coding: utf-8 -*-
"""
    lodgeit.urls
    ~~~~~~~~~~~~

    The URL mapping.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
from werkzeug.routing import Map, Rule

urlmap = Map(
    [
        # paste interface
        Rule('/', endpoint='pastes/new_paste'),
        Rule('/show/<int:paste_id>/', endpoint='pastes/show_paste'),
        Rule('/raw/<int:paste_id>/', endpoint='pastes/raw_paste'),
        Rule('/compare/', endpoint='pastes/compare_paste'),
        Rule('/compare/<int:new_id>/<int:old_id>/', endpoint='pastes/compare_paste'),
        Rule('/tree/<int:paste_id>/', endpoint='pastes/show_tree'),

        # paste list
        Rule('/all/', endpoint='pastes/show_all'),
        Rule('/all/<int:page>/', endpoint='pastes/show_all'),

        # xmlrpc
        Rule('/xmlrpc/', endpoint='xmlrpc/handle_request'),

        # static pages
        Rule('/about/', endpoint='static/about'),

        # colorscheme
        Rule('/colorscheme/', endpoint='pastes/set_colorscheme'),
    ],
)
