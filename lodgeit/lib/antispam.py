# -*- coding: utf-8 -*-
"""
    lodgeit.lib.antispam
    ~~~~~~~~~~~~~~~~~~~~

    Fight stupid spammers.

    :copyright: 2007 by Armin Ronacher, Christopher Grebs.
                2008 by Christopher Grebs.
    :license: BSD
"""
import re
from operator import sub
from itertools import starmap


_url_pattern = (
    r'(?:(?:https?|ftps?|file|ssh|mms|irc|rsync|smb)://|'
    r'(?:mailto|telnet|s?news|sips?|skype):)'
)

_link_re = re.compile(r'%s[^\s\'"]+\S' % _url_pattern)


def check_for_link_spam(code):
    """It's spam if more than 30% of the text are links."""
    spans = (x.span() for x in _link_re.finditer(code))
    return (sum(starmap(sub, spans)) * -100) / (len(code) or 1) > 30


def is_spam(code):
    """Check if the code provided contains spam."""
    return check_for_link_spam(code)
