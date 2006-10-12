from django.conf.urls.defaults import *
from django.conf import settings
from gallery.feeds import LatestPhotos, LatestPhotosByTag



media_path = settings.GALLERY_SETTINGS.get('media_path')
static_path = settings.GALLERY_SETTINGS.get('static_path')


feeds = {
    'latest': LatestPhotos,
    'tags': LatestPhotosByTag,
}


urls = [
    (r'^$', 'gallery.views.index'),
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),
    (r'^static/(.*)$', 'django.views.static.serve', {'document_root': static_path}),
    (r'^media/(.*)$', 'django.views.static.serve', {'document_root': media_path}),
    (r'^tag/(?P<tag_name>[\w\-]*)/$', 'gallery.views.photos_in_tag'),
    (r'^tag/(?P<tag_name>[\w\-]*)/(?P<page>\d+)/$', 'gallery.views.photos_in_tag'),
    (r'^photo/(?P<photo_id>\d+)/(?P<tag_name>[\w\-]*)/$', 'gallery.views.photos_in_tag'),
    (r'^photo/(?P<photo_id>\d+)/$', 'gallery.views.photo'),
]

urlpatterns = patterns('', *urls)
