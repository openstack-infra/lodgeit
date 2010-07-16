# -*- coding: utf-8 -*-
"""
    lodgeit.lib.compilerparser
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements parsers for compiler error messages.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD
"""
import re


_gcc_message_re = re.compile(r'''(?ux)
    ^\s*
        (?P<filename>[^:]*)
        :(?P<line>\d*)
        (:(?P<column>\d*))?
        ((\s*:)?\s*(?P<level>error|warning)\s*:)?
        \s(?P<message>.*)
    $
''')

_javac_message_re = re.compile(r'''(?ux)
    ^\s*
        (?P<filename>[^:]*)
        :(?P<line>\d*)
        (:(?P<column>\d*))?
        \s(?P<message>.*)
    $
''')
_javac_prefix_re = re.compile(r'^\s*\[javac\]\s')
_javac_junk_re = re.compile(r'^((Note:\s+.*?)|(\d+)\s+errors\s*)$')


class Raw(object):
    is_raw = True

    def __init__(self, raw):
        self.raw = raw


class Message(Raw):
    is_raw = False

    def __init__(self, raw, filename, lineno, column, message):
        Raw.__init__(self, raw)
        self.filename = filename
        self.lineno = lineno
        self.column = column
        self.message = message
        self.context = ''

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


def parse_javac_messages(data):
    """Parse javac messages."""
    result = []
    linebuffer = []

    def _remove_prefix(line):
        match = _javac_prefix_re.match(line)
        if match is not None:
            line = line[match.end():]
        return line

    def _append_buffered_lines():
        if not linebuffer:
            return
        if not result:
            result.append(Raw('\n'.join(linebuffer)))
        else:
            last = result[-1]
            last.raw = '\n'.join([last.raw] + linebuffer)
            if not last.is_raw:
                before = last.context and [last.context] or []
                last.context = '\n'.join(before + linebuffer)
        del linebuffer[:]

    lineiter = iter(data.splitlines())
    for line in lineiter:
        line = _remove_prefix(line)
        match = _javac_junk_re.match(line)
        if match is not None:
            _append_buffered_lines()
            result.append(Raw(line))
            continue
        match = _javac_message_re.match(line)
        if match is None:
            linebuffer.append(line)
        else:
            _append_buffered_lines()
            result.append(make_message(line, **match.groupdict()))

    _append_buffered_lines()
    return result
