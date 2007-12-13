# -*- coding: utf-8 -*-
"""
    lodgeit.controllers
    ~~~~~~~~~~~~~~~~~~~

    Module that helds the controllers

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""

class BaseController(object):
    """
    Base controller class. This does nothing *yet* but
    maybe is usefull later.
    """


def get_controller(name):
    cname, hname = name.split('/')
    module = __import__('lodgeit.controllers.' + cname, None, None, [''])
    controller = module.controller()
    return getattr(controller, hname)
