from pastebin.utils import templated
from django.http import HttpResponseRedirect
from pastebin.pastes.models import KNOWN_STYLES


@templated('static/help.html')
def help(request):
    return {}


@templated('static/about.html')
def about(request):
    return {}


@templated('static/error404.html')
def error404(request):
    return {
        'url':  '/' + request.META.get('PATH_INFO', '').lstrip('/')
    }


@templated('static/error500.html')
def error500(request):
    return {}


def change_settings(request):
    style = request.GET.get('style')
    if style in KNOWN_STYLES:
        request.session['style'] = style
    return HttpResponseRedirect(request.META.get('HTTP_REFERER') or '/')
