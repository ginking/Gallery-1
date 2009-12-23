from django.conf.urls.defaults import *
from django.conf import settings
from gallery.feeds import Photos, Tags, PhotosByTag, Comments

try:
    import django_openidconsumer
except ImportError:
    django_openidconsumer = None

feeds = {
    'comments': Comments,
    'photos': Photos,
    'tags': Tags,
    'tag': PhotosByTag,
}

urls = [
    (r'^$', 'gallery.views.index'),
    (r'^xmlrpc/$', 'gallery.xmlrpchandler.rpc_handler'),
    (r'^feeds/(?P<url>.*)/$',
     'django.contrib.syndication.views.feed', {'feed_dict': feeds}),
    (r'^tag/(?P<tag_name>[\w\+\-]*)/$', 'gallery.views.photos_in_tag'),
    (r'^tag/(?P<tag_name>[\w\+\-]*)/(?P<page>\d+)/$',
     'gallery.views.photos_in_tag'),
    (r'^photo/(?P<photo_id>\d+)/(?P<tag_name>[\w\-]*)/$',
     'gallery.views.photos_in_tag'),
    (r'^photo/(?P<photo_id>\d+)/$', 'gallery.views.photo'),
    (r'^date/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$',
     'gallery.views.date'),
    (r'^date/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<page>\d+)/$',
     'gallery.views.date'),
    (r'^popular/$', 'gallery.views.popular'),
    #(r'^popular/(?P<tag_name>[\w\+\-]*)/$', 'gallery.views.popular'),
    (r'^recent/$', 'gallery.views.recent'),
    (r'^recent/(?P<tag_name>[\w\+\-]*)/$', 'gallery.views.recent'),    
    (r'^recent/(?P<tag_name>[\w\+\-]*)/(?P<page>\d+)/$', 'gallery.views.recent'),
    ]

if django_openidconsumer:
    urls.extend([
    #(r'^comment/(?P<comment_id>\d+)/$', 'gallery.views.comment'),
    (r'^openid/$', 'django_openidconsumer.views.begin', {'sreg': 'fullname'}),
    (r'^openid/complete/$', 'django_openidconsumer.views.complete'),
    (r'^openid/signout/$', 'django_openidconsumer.views.signout'),
    (r'^status/cache/$', 'gallery.memcached_status.cache_status'),
])

media_path = settings.GALLERY_SETTINGS.get('media_path')
static_path = settings.GALLERY_SETTINGS.get('static_path')

if media_path:
    urls.append((r'^media/(.*)$',
                 'django.views.static.serve', {'document_root': media_path}))
if static_path:
    urls.append((r'^static/(.*)$',
                 'django.views.static.serve', {'document_root': static_path}))

urlpatterns = patterns('', *urls)
