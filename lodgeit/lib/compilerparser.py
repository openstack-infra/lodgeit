# -*- coding: utf-8 -*-
"""
    lodgeit.lib.compilerparser
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements parsers for compiler error messages.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD
"""
import re
from werkzeug import escape


_gcc_message_re = re.compile(r'''(?ux)
    ^\s*
        (?P<filename>[^:]*)
        :(?P<line>\d*)
        (:(?P<column>\d*))?
        ((\s*:)?\s*(?P<level>error|warning)\s*:)?
        \s(?P<message>.*)
    $
''')


class Message(object):

    def __init__(self, raw, filename, lineno, column, message):
        self.raw = raw
        self.filename = filename
        self.lineno = lineno
        self.column = column
        self.message = message

    @property
    def level(self):
        return self.__class__.__name__.lower()


class Warning(Message):
    pass


class Error(Message):
    pass


def make_message(raw, filename=None, line=None, column=None, level='error',
                 message=''):
    filename = filename or 'unknown'
    if level == 'error':
        cls = Error
    elif level == 'warning':
        cls = Warning
    else:
        cls = Message
    return cls(raw, filename, line, column, message)


def parse_gcc_messages(data):
    """Parse gcc messages."""
    result = []
    for line in data.splitlines():
        match = _gcc_message_re.match(line)
        if match is not None:
            result.append(make_message(line, **match.groupdict()))
    return result
