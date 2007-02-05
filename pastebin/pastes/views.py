# -*- coding: utf-8 -*-
"""
    pastebin.pastes.views
    ~~~~~~~~~~~~~~~~~~~~~

    Lodge It pastebin views.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD
"""
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.forms import FormWrapper
from pastebin.utils import Pagination, templated, render_diff, spam_check
from pastebin.pastes.models import Paste, Tag, tagify


@templated('pastes/new.html')
def new_paste(request, reply=None):
    tags = request.POST.get('tags', '')
    reply_to = None
    data = {}
    errors = {}

    if reply:
        reply_to = Paste.objects.get(uid=reply)
        data['title'] = reply_to.title
        if not data['title'].startswith('Re:'):
            data['title'] = 'Re: ' + data['title']
        data['language'] = reply_to.language
        data['code'] = reply_to.code
        data['private'] = reply_to.private
        tags = ' '.join(tag.name for tag in reply_to.tags.all())
        reply_to = reply_to.id

    manipulator = Paste.AddManipulator()
    if request.method == 'POST':
        data = request.POST.copy()
        if 'tags' in data:
            del data['tags']
        errors = manipulator.get_validation_errors(data)
        # negative captcha?
        if 'email' in data:
            errors = errors or data['email']
            del data['email']
        # spam words?
        if 'code' in data:
            errors = errors or spam_check(data['code'])
        if not errors:
            request.session['author'] = data['author']
            manipulator.do_html2python(data)
            paste = manipulator.save(data)
            for tag in tagify(tags):
                paste.tags.add(tag)
            return HttpResponseRedirect(paste.get_absolute_url())

    if not 'author' in data:
        data['author'] = request.session.get('author', '')

    return {
        'reply_to': reply_to,
        'tags':     tags,
        'form':     FormWrapper(manipulator, data, errors)
    }


@templated('pastes/show.html')
def show_paste(request, uid):
    paste = Paste.objects.get(uid=uid)
    if request.GET.get('action') == 'raw':
        return HttpResponse(paste.code, mimetype='text/plain')
    return {
        'paste':    paste
    }


@templated('pastes/tagcloud.html')
def tagcloud(request):
    return {
        'tags':     Tag.objects.all()
    }


@templated('pastes/taglist.html')
def taglist(request, tagname):
    return {
        'tag':      Tag.objects.get(name=tagname)
    }


@templated('pastes/all_pastes.html')
def all_pastes(request, page=1):
    pagination = Pagination(Paste.objects.order_by('-pub_date')
                                 .filter(private=False),
                            page, '/all/', 10)
    return {
        'pastes':       pagination.get_objects(),
        'pagination':   pagination.generate()
    }


def recent(request):
    """That's an old view"""
    return HttpResponseRedirect('/all/')


@templated('pastes/compare.html')
def compare_paste(request, uid):
    paste1 = Paste.objects.get(uid=uid)
    paste2 = paste1.reply_to
    if not paste2:
        raise Http404()
    diff = render_diff(paste2.code, paste1.code)
    return {
        'new':      paste1,
        'old':      paste2,
        'diff':     diff
    }


@templated('pastes/_autocomplete.html')
def autocomplete(request):
    return {
        'tags': Tag.objects.order_by('name')
                           .filter(name__istartswith=
                                   request.REQUEST.get('tags', ''))
    }


@templated('pastes/_find_thread.html')
def find_thread(request):
    paste = node = Paste.objects.get(uid=request.REQUEST.get('paste', ''))
    result = []
    while node.reply_to:
        result.append(node.reply_to)
        node = node.reply_to
    result.reverse()

    backref = paste
    while True:
        result.append(backref)
        try:
            backref = Paste.objects.get(reply_to=backref)
        except Paste.DoesNotExist:
            break
    result.reverse()

    return {
        'pastes':   result,
        'current':  paste
    }
