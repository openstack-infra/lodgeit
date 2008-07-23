# -*- coding: utf-8 -*-
"""
    lodgeit.lib.diff
    ~~~~~~~~~~~~~~~~

    Render a nice diff between two things.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD
"""
import re
from cgi import escape


def prepare_udiff(udiff):
    """Prepare an udiff for a template"""
    return DiffRenderer(udiff).prepare()


class DiffRenderer(object):
    """Give it a unified diff and it renders you a beautiful
    html diff :-)
    """
    _chunk_re = re.compile(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')

    def __init__(self, udiff):
        """:param udiff:   a text in udiff format"""
        self.lines = [escape(line) for line in udiff.splitlines()]

    def _extract_rev(self, line1, line2):
        try:
            if line1.startswith('--- ') and line2.startswith('+++ '):
                filename, old_rev = line1[4:].split(None, 1)
                new_rev = line2[4:].split(None, 1)[1]
                return filename, 'Old', 'New'
        except (ValueError, IndexError):
            pass
        return None, None, None

    def _highlight_line(self, line, next):
        """Highlight inline changes in both lines."""
        start = 0
        limit = min(len(line['line']), len(next['line']))
        while start < limit and line['line'][start] == next['line'][start]:
            start += 1
        end = -1
        limit -= start
        while -end <= limit and line['line'][end] == next['line'][end]:
            end -= 1
        end += 1
        if start or end:
            def do(l):
                last = end + len(l['line'])
                if l['action'] == 'add':
                    tag = 'ins'
                else:
                    tag = 'del'
                l['line'] = u'%s<%s>%s</%s>%s' % (
                    l['line'][:start],
                    tag,
                    l['line'][start:last],
                    tag,
                    l['line'][last:]
                )
            do(line)
            do(next)

    def _parse_udiff(self):
        """Parse the diff an return data for the template."""
        lineiter = iter(self.lines)
        files = []
        try:
            line = lineiter.next()
            while True:
                # continue until we found the old file
                if not line.startswith('--- '):
                    line = lineiter.next()
                    continue

                chunks = []
                filename, old_rev, new_rev = \
                    self._extract_rev(line, lineiter.next())
                files.append({
                    'filename':         filename,
                    'old_revision':     old_rev,
                    'new_revision':     new_rev,
                    'chunks':           chunks
                })

                line = lineiter.next()
                while line:
                    match = self._chunk_re.match(line)
                    if not match:
                        break

                    lines = []
                    chunks.append(lines)

                    old_line, old_end, new_line, new_end = \
                        [int(x or 1) for x in match.groups()]
                    old_line -= 1
                    new_line -= 1
                    old_end += old_line
                    new_end += new_line
                    line = lineiter.next()

                    while old_line < old_end or new_line < new_end:
                        if line:
                            command, line = line[0], line[1:]
                        else:
                            command = ' '
                        affects_old = affects_new = False

                        if command == ' ':
                            affects_old = affects_new = True
                            action = 'unmod'
                        elif command == '+':
                            affects_new = True
                            action = 'add'
                        elif command == '-':
                            affects_old = True
                            action = 'del'
                        else:
                            # this happens sometimes if it's a diff from
                            # a po/pot file with `"` at one line.
                            # No idea how to handle that a better way...
                            if command == '"':
                                affects_old = affects_new = True
                                action = 'unmod'
                                line = '"'
                            else:
                                raise RuntimeError()

                        old_line += affects_old
                        new_line += affects_new
                        lines.append({
                            'old_lineno':   affects_old and old_line or u'',
                            'new_lineno':   affects_new and new_line or u'',
                            'action':       action,
                            'line':         line
                        })
                        line = lineiter.next()

        except StopIteration:
            pass

        # highlight inline changes
        for file in files:
            for chunk in chunks:
                lineiter = iter(chunk)
                first = True
                try:
                    while True:
                        line = lineiter.next()
                        if line['action'] != 'unmod':
                            nextline = lineiter.next()
                            if nextline['action'] == 'unmod' or \
                               nextline['action'] == line['action']:
                                continue
                            self._highlight_line(line, nextline)
                except StopIteration:
                    pass

        return files

    def prepare(self):
        return self._parse_udiff()
