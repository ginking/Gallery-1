from django.conf.urls.defaults import *
from django.conf import settings
from gallery.feeds import Photos, Tags, PhotosByTag, Comments

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
    (r'^comment/(?P<comment_id>\d+)/$', 'gallery.views.comment'),
]

media_path = settings.GALLERY_SETTINGS.get('media_path')
static_path = settings.GALLERY_SETTINGS.get('static_path')

if media_path:
    urls.append((r'^media/(.*)$',
                 'django.views.static.serve', {'document_root': media_path}))
if static_path:
    urls.append((r'^static/(.*)$',
                 'django.views.static.serve', {'document_root': static_path}))

urlpatterns = patterns('', *urls)
