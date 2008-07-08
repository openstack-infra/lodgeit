# -*- coding: utf-8 -*-
"""
    lodgeit.controllers
    ~~~~~~~~~~~~~~~~~~~

    Module that helds the controllers

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""

def get_controller(name):
    cname, hname = name.split('/')
    module = __import__('lodgeit.controllers.' + cname, None, None, [''])
    controller = module.controller()
    return getattr(controller, hname)
