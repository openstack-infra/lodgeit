# -*- coding: utf-8 -*-
"""
    lodgeit.lib.antispam
    ~~~~~~~~~~~~~~~~~~~~

    Fight stupid spammers.

    :copyright: 2007-2008 by Armin Ronacher, Christopher Grebs.
    :license: BSD
"""
from __future__ import division
import re
from operator import sub
from itertools import starmap


_url_pattern = (
    r'(?:(?:https?|ftps?|file|ssh|mms|irc|rsync|smb)://|'
    r'(?:mailto|telnet|s?news|sips?|skype):)'
)

_link_re = re.compile(r'%s[^\s\'"]+\S' % _url_pattern)


# maximum number of links in percent
MAX_LINK_PERCENTAGE = 30

# maximum number of links in the text (hard limit)
MAX_LINK_NUMBER = 15


def check_for_link_spam(code):
    """It's spam if more than 30% of the text are links."""
    spans = [x.span() for x in _link_re.finditer(code)]
    if len(spans) > MAX_LINK_PERCENTAGE:
        return True
    return (sum(starmap(sub, spans)) * -100) / (len(code) or 1) \
           > MAX_LINK_PERCENTAGE


def is_spam(code):
    """Check if the code provided contains spam."""
    return check_for_link_spam(code)
