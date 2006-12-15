from re import escape
from django.conf import settings
from django.conf.urls.defaults import *


urlpatterns = patterns('',
    # Index
    (r'^$', 'pastebin.pastes.views.new_paste'),
    (r'^reply/([^/]+)/$', 'pastebin.pastes.views.new_paste'),
    (r'^show/([^/]+)/$', 'pastebin.pastes.views.show_paste'),
    (r'^compare/([^/]+)/$', 'pastebin.pastes.views.compare_paste'),
    (r'^tags/$', 'pastebin.pastes.views.tagcloud'),
    (r'^tags/([^/]+)/$', 'pastebin.pastes.views.taglist'),
    (r'recent/$', 'pastebin.pastes.views.recent'),
    (r'^all/$', 'pastebin.pastes.views.all_pastes'),
    (r'^all/(\d+)/$', 'pastebin.pastes.views.all_pastes'),

    # Static Pages
    (r'^change_settings/$', 'pastebin.static.views.change_settings'),
    (r'^about/$', 'pastebin.static.views.about'),
    (r'^help/$', 'pastebin.static.views.help'),

    # Ajax Functions
    (r'^ajax/tags_auto_complete/$', 'pastebin.pastes.views.autocomplete'),
    (r'^ajax/find_paste_thread/$', 'pastebin.pastes.views.find_thread'),

    # XMLRPC
    (r'^xmlrpc/$', 'pastebin.xmlrpc.views.handle_request'),

    # Admin and Media
    (r'^%s/(.*)$' % escape(settings.MEDIA_URL.strip('/')),
     'django.views.static.serve', {
        'document_root':    settings.MEDIA_ROOT
    }),
    (r'^%s/(.*)$' % escape(settings.ADMIN_MEDIA_PREFIX.strip('/')),
     'django.views.static.serve', {
         'document_root':   settings.ADMIN_MEDIA_ROOT
    }),
    (r'^admin/', include('django.contrib.admin.urls')),
)

handler404 = 'pastebin.static.views.error404'
handler500 = 'pastebin.static.views.error500'
