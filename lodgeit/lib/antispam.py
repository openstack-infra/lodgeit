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
import urllib
import time
from datetime import datetime, timedelta


_url_pattern = (
    r'(?:(?:https?|ftps?|file|ssh|mms|irc|rsync|smb)://|'
    r'(?:mailto|telnet|s?news|sips?|skype):)'
)

LINK_RE = re.compile(r'%s[^\s\'"]+\S' % _url_pattern)


def percentize(matched, length):
    return matched * 100.0 / (length or 1)


class AntiSpam(object):
    """Class for fighting against that damn spammers. It's working not with
    a flat file with some bad-content but with some other hopefully more
    effective methods.
    """

    def check_for_link_spam(self, code):
        lengths = (x.span() for x in LINK_RE.finditer(code))
        return percentize(sum(i[1]-i[0] for i in lengths),
                          len(code)) > 50

    def is_spam(self, code):
        """Check if one of the fields provides contains spam."""
        return self.check_for_link_spam(code)
