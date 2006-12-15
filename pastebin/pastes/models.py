# -*- coding: utf-8 -*-
"""
    pastebin.pastes.models
    ~~~~~~~~~~~~~~~~~~~~~~

    Lodge It pastebin models.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD
"""
import sha
import math
import re
from pastebin.utils import get_external_url, get_timestamp
from django.db import models
from time import time
from random import random
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, LEXERS
from pygments.styles import STYLE_MAP

LANGUAGES = [(x[2][0], x[1]) for x in LEXERS.itervalues()]
LANGUAGES.sort(key=lambda x: x[1].lower())

LANGUAGE_DICT = dict(LANGUAGES)

STYLES = [(x, x.title()) for x in STYLE_MAP]
STYLES.sort(key=lambda x: x[0].lower())
KNOWN_STYLES = set(STYLE_MAP)

formatter = HtmlFormatter(cssclass='syntax',
                          linenos=True,
                          linenospecial=5)


tag_strip_re = re.compile(r'[^a-zA-Z0-9][^a-zA-Z0-9_-]*')


def tagify(taglist):
    """
    Ensures that only good tag names are submitted and return
    an iterator of ``Tag`` objects.
    """
    if isinstance(taglist, (tuple, list)):
        names = taglist
    else:
        names = taglist.split()
    found = set()
    for name in names:
        name = tag_strip_re.sub('', name).lower()
        if name not in found:
            found.add(name)
            yield Tag.objects.get_or_create(name=name)[0]


def get_next_paste_uid(private):
    """
    Return the next free uid for a Paste. If private is ``True``
    the returned uid will be a 40bit long hash value, otherwise
    a integer number as string.
    """
    if private:
        while True:
            uid = sha.new('%s|%s' % (time(), random())).hexdigest()
            try:
                Paste.objects.get(uid=uid)
            except Paste.DoesNotExist:
                return uid
    try:
        last = Paste.objects.order_by('-id').filter(private=False)[0]
    except IndexError:
        return '1'
    return str(int(last.uid) + 1)


class TagManager(models.Manager):

    def get_popular(self, amount=15):
        all = list(self.all())
        all.sort(key=lambda x: x.count())
        all.reverse()
        return all[:amount]


class Tag(models.Model):
    name = models.CharField(maxlength=100)
    objects = TagManager()

    def get_absolute_url(self):
        return '/tags/%s/' % self.name

    def get_size(self):
        return (math.log(self.count() or 1) * 4) + 10

    def count(self):
        return self.paste_set.count()

    def __str__(self):
        return self.name

    class Admin:
        list_display = search_fields = ('name',)

    class Meta:
        ordering = ('-name',)


class Paste(models.Model):
    uid = models.CharField(maxlength=40, blank=True)
    private = models.BooleanField()
    title = models.CharField(maxlength=200, blank=True)
    author = models.CharField(maxlength=100, blank=True)
    pub_date = models.DateTimeField(auto_now_add=True)
    reply_to = models.ForeignKey('self', blank=True, null=True)
    language = models.CharField(maxlength=50, choices=LANGUAGES,
                                blank=True)
    code = models.TextField()
    parsed_code = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True)

    @property
    def language_name(self):
        return LANGUAGE_DICT.get(self.language, 'Unknown')

    @property
    def code_summary(self):
        try:
            start = self.parsed_code.index('</pre>')
            code = self.parsed_code[
                self.parsed_code.index('<pre>', start) + 5:
                self.parsed_code.rindex('</pre>')
            ].strip('\n').splitlines()
        except IndexError:
            code = ''.strip('\n').splitlines()
        code = '\n'.join(code[:7] + ['...'])
        return '<div class="syntax"><pre>%s</pre></div>' % code

    def to_dict(self):
        return {
            'uid':              self.uid,
            'private':          self.private,
            'title':            self.title,
            'author':           self.author,
            'pub_date':         get_timestamp(self.pub_date),
            'reply_to':         getattr(self.reply_to, 'uid', ''),
            'language':         self.language,
            'language_name':    self.language_name,
            'code':             self.code,
            'parsed_code':      self.parsed_code,
            'tags':             [tag.name for tag in self.tags.all()],
            'url':              get_external_url(self)
        }

    def get_absolute_url(self):
        return '/show/%s/' % self.uid

    def get_reply_url(self):
        return '/reply/%s/' % self.uid

    def get_compare_url(self):
        if self.reply_to:
            return '/compare/%s/' % self.uid
        return ''

    def save(self):
        if not self.title:
            self.title = 'Untitled'
        if not self.author:
            self.author = 'anonymous'
        if not self.uid:
            self.uid = get_next_paste_uid(self.private)
        if not self.language:
            self.language = 'text'
        lexer = get_lexer_by_name(self.language)
        self.code = '\n'.join(self.code.splitlines())
        self.parsed_code = highlight(self.code, lexer, formatter)
        super(Paste, self).save()

    def __str__(self):
        return 'Paste #%s by %s' % (
            self.uid,
            self.author
        )

    class Admin:
        fields = (
            (None, {
                'fields':   ('title', 'author', 'pub_date', 'language',
                             'code')
            }),
            ('Extra', {
                'fields':   ('uid', 'private', 'reply_to')
            })
        )
        list_display = ('uid', 'title', 'author', 'pub_date', 'language')
        list_filter = ('language', 'pub_date')
        search_fields = ('code', 'author', 'title')

    class Meta:
        ordering = ('-pub_date', 'title')
