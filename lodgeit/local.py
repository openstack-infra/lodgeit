# -*- coding: utf-8 -*-
"""
    lodgeit.utils
    ~~~~~~~~~~~~~

    Serveral utilities used by LodgeIt.

    :copyright: 2008 by Christopher Grebs.
    :license: BSD
"""
from werkzeug import Local, LocalManager, LocalProxy

#: context locals
ctx = Local()
_local_manager = LocalManager(ctx)

#: local objects
request = LocalProxy(ctx, 'request')
application = LocalProxy(ctx, 'application')
