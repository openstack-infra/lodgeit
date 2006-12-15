# -*- coding: utf-8 -*-
"""
    pastebin.xmlrpc.views
    ~~~~~~~~~~~~~~~~~~~~~

    Lodge It pastebin xmlrpc interface.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD
"""
from pygments.lexers import get_lexer_by_name, \
                            get_lexer_for_mimetype, \
                            get_lexer_for_filename
from pygments.formatters import HtmlFormatter
from pastebin.utils import templated, xmlrpc, external, get_timestamp, \
                           get_external_url
from pastebin.pastes.models import Paste, Tag, LANGUAGES, LANGUAGE_DICT, \
                                   KNOWN_STYLES, tagify


@external('pastes.getLanguages')
def pastes_get_supported_languages():
    """Return an array of supported languages.
    
    The returned array is an array of (key, value)
    arrays, where key is one of the internal language
    names and value the human readable name.
    """
    return LANGUAGES


@external('pastes.getNameByAlias')
def pastes_get_name_by_alias(alias):
    """Return the human readable name of an language by
    alias or return an empty string in case of failure."""
    try:
        lexer = get_lexer_by_name(alias)
    except ValueError:
        return ''
    return lexer.name


@external('pastes.getAliasForMimetype')
def pastes_get_alias_for_mimetype(mimetype):
    """Return the alias for an lexer for a mimetype or
    an empty string if not found."""
    try:
        lexer = get_lexer_for_mimetype(mimetype)
    except ValueError:
        return ''
    return lexer.aliases[0]


@external('pastes.getAliasForFilename')
def pastes_get_alias_for_filename(filename):
    """Return the alias for a filename. If not found
    the return value will be an empty string."""
    try:
        lexer = get_lexer_for_filename(filename)
    except ValueError:
        return ''
    return lexer.aliases[0]


@external('pastes.pasteExists')
def pastes_paste_exists(uid):
    """Check if a paste exists."""
    try:
        Paste.objects.get(uid=uid)
    except Paste.DoesNotExist:
        return False
    return True


@external('pastes.getPaste')
def pastes_get_paste(uid):
    """Return the details of a paste for a given
    uid as an hash. If the paste is not found the
    return value is boolean false.
    
    Note that the uid is in fact a string!"""
    try:
        if not isinstance(uid, basestring):
            uid = None
        paste = Paste.objects.get(uid=uid)
    except Paste.DoesNotExist:
        return False
    return paste.to_dict()


@external('pastes.getURL')
def pastes_get_url(uid):
    """Return the url to the paste or an empty
    string if the paste does not exists."""
    try:
        return get_external_url(Paste.objects.get(uid=uid))
    except Paste.DoesNotExists:
        return ''


@external('pastes.getRecent')
def pastes_get_recent(n=1):
    """Return a list of the recent 'n' pastes.
    The maximal allowed number is 50. Note that private
    pastes won't be part of that list."""
    n = min(50, n)
    return [paste.to_dict() for paste in
            Paste.objects.filter(private=False)[:n]]


@external('pastes.getPastesForTag')
def get_pastes_for_tag(tagname):
    """Return all pastes for a tag."""
    try:
        tag = Tag.objects.get(name=tagname)
    except Tag.DoesNotExist:
        return []
    return [p.to_dict() for p in tag.paste_set.all()]


@external('pastes.newPaste')
def pastes_new_paste(language, code, private=False, title='Untitled',
                     author='anonymous', tags=[]):
    """Create a new paste. language must be a known alias,
    code the piece of code you want to upload, private a
    boolean indicating if you want a private upload, title
    and author are strings for the details and tags a list
    of tag names for this paste.
    
    Return 0 if something goes wrong, else an dict with the
    uid and url."""
    try:
        if not code.strip():
            raise ValueError()
        paste = Paste(
            language=language,
            code=code,
            private=private,
            title=title,
            author=author,
        )
        paste.save()
    except:
        return 0
    for tag in tagify(tags):
        paste.tags.add(tag)
    return {
        'uid':      paste.uid,
        'url':      get_external_url(paste)
    }


@external('pastes.countPastes')
def pastes_count_pastes():
    """Return the total amount of pastes."""
    return Paste.objects.count()


@external('pastes.countPrivate')
def pastes_count_private():
    """Return the total amount of private pastes."""
    return Paste.objects.filter(private=True).count()


@external('pastes.countPublic')
def pastes_count_public():
    """Return the total amount of public pastes."""
    return Paste.objects.filter(private=False).count()


@external('styles.getStyle')
def styles_get_style(name, prefix=''):
    """Return a string containing CSS rules for the CSS classes
    used by the formatter.
    
    The argument prefix can be used to
    specify additional CSS selectors that are prepended to the
    classes.
    """
    try:
        formatter = HtmlFormatter(style=name)
    except ValueError:
        return ''
    return formatter.get_style_defs(prefix)


@external('styles.getStyleList')
def styles_get_style_list():
    """Return a list of known styles."""
    return sorted(KNOWN_STYLES)


@external('styles.styleExists')
def styles_style_exists(name):
    """Check if a style exists."""
    return name in KNOWN_STYLES


@external('tags.getTagCloud')
def tags_get_tag_cloud():
    """Return a tag cloud (unsorted)"""
    return [{
        'name':     tag.name,
        'size':     tag.get_size(),
        'count':    tag.count()
    } for tag in Tag.objects.all()]


@templated('xmlrpc/index.html')
def handle_request(request):
    if request.method == 'POST':
        return xmlrpc.handle_request(request)
    return {
        'methods':          xmlrpc.get_public_methods(),
        'interface_url':    'http://%s/xmlrpc/' % request.META['SERVER_NAME']
    }
