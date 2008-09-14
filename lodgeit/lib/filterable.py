#-*- coding: utf-8 -*-
"""
    lodgeit.libs.filterable
    ~~~~~~~~~~~~~~~~~~~~~~~

    Small library that adds filterable support to some parts of lodgeit.

    :copyright: 2008 by Christopher Grebs.
    :license: BSD.
"""
from lodgeit.i18n import _
from lodgeit.utils import render_template


ACTIONS = {
    'str': {
        'is':           _(u'is'),
        'contains':     _(u'contains'),
        'startswith':   _('startswith'),
    },
    'int': {
        'is':           _(u'is'),
        'greater':      _(u'greater'),
        'lower':        _(u'lower'),
    },
    'date': {
        'is':           _(u'same date'),
        'greater':      _(u'later'),
        'lower':        _(u'earlier'),
    }
}
ACTIONS_MAP = {
    'is':         lambda f, v: f == v,
    'contains':   lambda f, v: f.contains(v),
    'startswith': lambda f, v: f.startswith(v),
    'greater':    lambda f, v: f > v,
    'lower':      lambda f, v: f < v,
    'bool':       lambda f, v: f == (v == 'true'),
}


class Filterable(object):

    def __init__(self, model, objects, fields, args, inline=False):
        self.model = model
        self.fields = fields
        self.objects = objects
        self.args = args
        self.filters = {}
        for field in fields:
            action = args.get('%s_action' % field)
            value = args.get('%s_value' % field)
            if action and value and action in ACTIONS_MAP \
                    and not field == args.get('remove_filter'):
                self.filters[field] = action, value

        new_filter = args.get('new_filter')
        if 'add_filter' in args and new_filter and new_filter in fields:
            self.filters[new_filter] = 'is', ''

        self.inline = inline

    def get_html(self):
        ret = render_template('utils/filterable.html', plain=True, **{
            'filters': self.filters,
            'fields':  self.fields,
            'actions': ACTIONS,
            'args':    {'order': self.args.get('order')},
            'inline':  self.inline
        })
        return ret

    def get_objects(self):
        for field, filter in self.filters.iteritems():
            action, value = filter
            if value:
                func = ACTIONS_MAP[action]
                criterion = (getattr(self.model, field), value)
                self.objects = self.objects.filter(func(*criterion))
        return self.objects
