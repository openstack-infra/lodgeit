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
    Base controller. add some stuff to the dict on instanciation
    """

    def __init__(self, req):
        self.request = req
        self.app = req.app
        self.engine = req.engine
        self.dbsession = req.dbsession


def get_controller(name, req):
    cname, hname = name.split('/')
    module = __import__('lodgeit.controllers.' + cname, None, None, [''])
    controller = module.controller(req)
    return getattr(controller, hname)
