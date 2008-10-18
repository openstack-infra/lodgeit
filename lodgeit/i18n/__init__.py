# -*- coding: utf-8 -*-
"""
    lodgeit.i18n
    ~~~~~~~~~~~~

    i18n tools for LodgeIt!

    :copyright: Copyright 2008 by Armin Ronacher, Christopher Grebs.
    :license: GNU GPL.
"""
import os
from babel import Locale, dates, UnknownLocaleError
from babel.support import Translations

from lodgeit import local


_translations = {}


def get_translations(locale):
    """Get the translation for a locale."""
    locale = Locale.parse(locale)
    translations = _translations.get(str(locale))
    if translations is not None:
        return translations
    rv = Translations.load(os.path.dirname(__file__), [locale])
    _translations[str(locale)] = rv
    return rv


def gettext(string):
    """Translate the given string to the language of the application."""
    request = getattr(local, 'request', None)
    if not request:
        return string
    return request.translations.ugettext(string)


def ngettext(singular, plural, n):
    """Translate the possible pluralized string to the language of the
    application.
    """
    request = getattr(local, 'request', None)
    if not request:
        if n == 1:
            return singular
        return plural
    return request.translations.ungettext(singular, plural, n)


def format_datetime(datetime=None, format='medium'):
    """Return a date formatted according to the given pattern."""
    return _date_format(dates.format_datetime, datetime, format)


def list_languages():
    """Return a list of all languages."""
    languages = [('en', Locale('en').display_name)]
    folder = os.path.dirname(__file__)

    for filename in os.listdir(folder):
        if filename == 'en' or not \
           os.path.isdir(os.path.join(folder, filename)):
            continue
        try:
            l = Locale.parse(filename)
        except UnknownLocaleError:
            continue
        languages.append((str(l), l.display_name))

    languages.sort(key=lambda x: x[1].lower())
    return languages


def has_language(language):
    """Check if a language exists."""
    return language in dict(list_languages())


def _date_format(formatter, obj, format):
    request = getattr(local, 'request', None)
    if request:
        locale = request.locale
    else:
        locale = Locale('en')
    return formatter(obj, format, locale=locale)


class _TranslationProxy(object):
    """Class for proxy strings from gettext translations.  This is a helper
    for the lazy_* functions from this module.

    The proxy implementation attempts to be as complete as possible, so that
    the lazy objects should mostly work as expected, for example for sorting.
    """
    __slots__ = ('_func', '_args')

    def __init__(self, func, *args):
        self._func = func
        self._args = args

    value = property(lambda x: x._func(*x._args))

    def __contains__(self, key):
        return key in self.value

    def __nonzero__(self):
        return bool(self.value)

    def __dir__(self):
        return dir(unicode)

    def __iter__(self):
        return iter(self.value)

    def __len__(self):
        return len(self.value)

    def __str__(self):
        return str(self.value)

    def __unicode__(self):
        return unicode(self.value)

    def __add__(self, other):
        return self.value + other

    def __radd__(self, other):
        return other + self.value

    def __mod__(self, other):
        return self.value % other

    def __rmod__(self, other):
        return other % self.value

    def __mul__(self, other):
        return self.value * other

    def __rmul__(self, other):
        return other * self.value

    def __lt__(self, other):
        return self.value < other

    def __le__(self, other):
        return self.value <= other

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return self.value != other

    def __gt__(self, other):
        return self.value > other

    def __ge__(self, other):
        return self.value >= other

    def __getattr__(self, name):
        if name == '__members__':
            return self.__dir__()
        return getattr(self.value, name)

    def __getitem__(self, key):
        return self.value[key]

    def __repr__(self):
        try:
            return 'i' + repr(unicode(self.value))
        except:
            return '<%s broken>' % self.__class__.__name__


def lazy_gettext(string):
    """A lazy version of `gettext`."""
    return _TranslationProxy(gettext, string)


def lazy_ngettext(singular, plural, n):
    """A lazy version of `ngettext`"""
    return _TranslationProxy(ngettext, singular, plural, n)


_ = gettext
