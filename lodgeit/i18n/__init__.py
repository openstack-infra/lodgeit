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



def load_translations(locale):
    """Load the translation for a locale."""
    return Translations.load(os.path.dirname(__file__), [locale])


def gettext(string):
    """Translate the given string to the language of the application."""
    if not local.application:
        return string
    return local.application.translations.ugettext(string)


def ngettext(singular, plural, n):
    """Translate the possible pluralized string to the language of the
    application.
    """
    if not local.application:
        if n == 1:
            return singular
        return plural
    return local.application.translations.ungettext(singular, plural, n)


def format_datetime(datetime=None, format='medium'):
    """Return a date formatted according to the given pattern."""
    return _date_format(dates.format_datetime, datetime, format)


def list_languages():
    """Return a list of all languages."""
    if local.application:
        locale = local.application.locale
    else:
        locale = Locale('en')

    languages = [('en', Locale('en').get_display_name(locale))]
    folder = os.path.dirname(__file__)

    for filename in os.listdir(folder):
        if filename == 'en' or not \
           os.path.isdir(os.path.join(folder, filename)):
            continue
        try:
            l = Locale.parse(filename)
        except UnknownLocaleError:
            continue
        languages.append((str(l), l.get_display_name(locale)))

    languages.sort(key=lambda x: x[1].lower())
    return languages


def has_language(language):
    """Check if a language exists."""
    return language in dict(list_languages())


def _date_format(formatter, obj, format):
    if not local.application:
        locale = Locale('en')
    else:
        locale = local.application.locale
    return formatter(obj, format, locale=locale)


_ = gettext
