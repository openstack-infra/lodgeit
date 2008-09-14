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


_ = gettext
