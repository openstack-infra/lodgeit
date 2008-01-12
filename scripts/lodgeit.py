#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    LodgeIt!
    ~~~~~~~~

    A script that pastes stuff into the lodgeit pastebin on
    paste.pocoo.org.

    .lodgeitrc / _lodgeitrc
    -----------------------

    Under UNIX create a file called ``~/.lodgerc``, under Windows
    create a file ``%APPDATA%/_lodgerc`` to override defaults::

        language=default_language
        clipboard=true/false
        open_browser=true/false
        encoding=fallback_charset

    :authors: 2007 Georg Brandl <georg@python.org>,
              2006 Armin Ronacher <armin.ronacher@active-4.com>,
              2006 Matt Good <matt@matt-good.net>,
              2005 Raphael Slinckx <raphael@slinckx.net>
"""
import os
import sys


SCRIPT_NAME = os.path.basename(sys.argv[0])
VERSION = '0.2'
SERVICE_URL = 'http://paste.pocoo.org/'
SETTING_KEYS = ['author', 'title', 'language', 'private', 'clipboard',
                'open_browser']


def fail(msg, code):
    print >> sys.stderr, 'ERROR: %s' % msg
    sys.exit(code)


def load_default_settings():
    """Load the defaults from the lodgeitrc file."""
    settings = {
        'language':     None,
        'clipboard':    True,
        'open_browser': False,
        'encoding':     'iso-8859-15'
    }
    rcfile = None
    if os.name == 'posix':
        rcfile = os.path.expanduser('~/.lodgeitrc')
    elif os.name == 'nt' and 'APPDATA' in os.environ:
        rcfile = os.path.expandvars(r'$APPDATA\_lodgeitrc')
    if rcfile:
        try:
            f = open(rcfile)
            for line in f:
                if line.strip()[:1] in '#;':
                    continue
                p = line.split('=', 1)
                if len(p) == 2:
                    key = p[0].strip().lower()
                    if key in settings:
                        if key in ('clipboard', 'open_browser'):
                            settings[key] = p[1].strip().lower() in \
                                            ('true', '1', 'on', 'yes')
                        else:
                            settings[key] = p[1].strip()
            f.close()
        except IOError:
            pass
    settings['tags'] = []
    settings['title'] = None
    return settings


def make_utf8(text, encoding):
    """Convert a text to utf-8"""
    try:
        u = unicode(text, 'utf-8')
        uenc = 'utf-8'
    except UnicodeError:
        try:
            u = unicode(text, encoding)
            uenc = 'utf-8'
        except UnicodeError:
            u = unicode(text, 'iso-8859-15', 'ignore')
            uenc = 'iso-8859-15'
    try:
        import chardet
    except ImportError:
        return u.encode('utf-8')
    d = chardet.detect(text)
    if d['encoding'] == uenc:
        return u.encode('utf-8')
    return unicode(text, d['encoding'], 'ignore').encode('utf-8')


def get_xmlrpc_service():
    global _xmlrpc_service
    import xmlrpclib
    try:
        _xmlrpc_service
    except NameError:
        try:
            _xmlrpc_service = xmlrpclib.ServerProxy(SERVICE_URL + 'xmlrpc/',
                                                    allow_none=True)
        except:
            fail('Could not connect to Pastebin', -1)
    return _xmlrpc_service


def copy_url(url):
    """Copy the url into the clipboard."""
    try:
        import win32clipboard
        import win32con
    except ImportError:
        try:
            import pygtk
            pygtk.require('2.0')
            import gtk
            import gobject
        except ImportError:
            return
        gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD).set_text(url)
        gobject.idle_add(gtk.main_quit)
        gtk.main()
    else:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(url)
        win32clipboard.CloseClipboard()


def open_webbrowser(url):
    """Open a new browser window."""
    import webbrowser
    webbrowser.open(url)


def language_exists(language):
    """Check if a language alias exists."""
    xmlrpc = get_xmlrpc_service()
    langs = xmlrpc.pastes.getLanguages()
    return language in [x[0] for x in langs]


def get_mimetype(data, filename):
    """Try to get MIME type from data."""
    try:
        import gnomevfs
    except ImportError:
        pass
    else:
        if filename:
            return gnomevfs.get_mime_type(os.path.abspath(filename))
        return gnomevfs.get_mime_type_for_data(data)


def print_languages():
    xmlrpc = get_xmlrpc_service()
    languages = xmlrpc.pastes.getLanguages()
    languages.sort(lambda a, b: cmp(a[1].lower(), b[1].lower()))
    print 'Supported Languages:'
    for alias, name in languages:
        print '    %-30s%s' % (alias, name)


def download_paste(uid):
    xmlrpc = get_xmlrpc_service()
    paste = xmlrpc.pastes.getPaste(uid)
    if not paste:
        fail('Paste "%s" does not exist' % uid, 5)
    print paste['code'].encode('utf-8')


def create_paste(code, language, filename, mimetype):
    xmlrpc = get_xmlrpc_service()
    rv = xmlrpc.pastes.newPaste(language, code, None, filename, mimetype)
    if not rv:
        fail('Could not commit paste. Something went wrong', 4)
    return rv


if __name__ == '__main__':
    # parse command line
    from optparse import OptionParser
    parser = OptionParser()

    settings = load_default_settings()

    parser.add_option('-v', '--version', action='store_true',
                      help='Print script version')
    parser.add_option('-l', '--language', default=settings['language'],
                      help='Used syntax highlighter for the file')
    parser.add_option('-e', '--encoding', default=settings['encoding'],
                      help='Specify the encoding of a file (default is '
                           'utf-8 or guessing if available)')
    parser.add_option('--no-clipboard', dest='clipboard',
                      action='store_false',
                      default=settings['clipboard'],
                      help="Don't copy the url into the clipboard")
    parser.add_option('--open-browser', dest='open_browser',
                      action='store_true',
                      default=settings['open_browser'],
                      help='Open the paste in a web browser')
    parser.add_option('--languages', action='store_true', default=False,
                      help='Retrieve a list of supported languages')
    parser.add_option('--download', metavar='UID',
                      help='Download a given paste')

    opts, args = parser.parse_args()

    if len(args) > 1:
        fail('Can only paste one file', 1)

    # System Version
    if opts.version:
        print '%s: version %s' % (SCRIPT_NAME, VERSION)
        sys.exit()

    # Languages
    elif opts.languages:
        print_languages()
        sys.exit()

    # Download Paste
    elif opts.download:
        download_paste(opts.download)
        sys.exit()

    # check language if given
    if opts.language and not language_exists(opts.language):
        fail('Language %s is not supported' % opts.language, 3)

    # load file
    try:
        if args:
            f = file(args[0], 'r')
        else:
            f = sys.stdin
        data = f.read()
        f.close()
    except Exception, msg:
        fail('Error while reading the file: %s' % msg, 2)
    if not data.strip():
        fail('Aborted, paste file was empty', 4)

    # fill with default settings
    mimetype = ''
    filename = args and args[0] or ''
    if not opts.language:
        opts.language = ''
        mimetype = get_mimetype(data, filename) or ''

    # create paste
    code = make_utf8(data, opts.encoding)
    id = create_paste(code, opts.language, filename, mimetype)
    url = '%sshow/%d' % (SERVICE_URL, id)
    print url
    if opts.open_browser:
        open_webbrowser(url)
    if opts.clipboard:
        copy_url(url)
