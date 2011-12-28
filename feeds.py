from django.contrib.syndication.feeds import Feed
from gallery.models import Tag, Photo, Video
from gallery.addon_models import Comment
from django.core.exceptions import ObjectDoesNotExist

class Photos(Feed):
    title = "Photos recently added"
    link = "/gallery/"
    description = title

    def items(self):
        return Photo.objects.using("gallery").order_by('-timestamp')[:15]

class Videos(Feed):
    title = "Videos recently added"
    link = "/gallery/"
    description = title

    def items(self):
        return Video.objects.using("gallery").order_by('-time_created')[:15]

class Tags(Feed):
    title = "Tags recently updated"
    link = "/gallery/"
    description = "Tags recently updated"

    def items(self):
        return Tag.get_recent_tags_cloud()

class TagContents(Feed):

    def get_object(self, bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return Tag.with_name(bits[0])

    def title(self, obj):
        return "Medias tagged with %s" % obj.name

    def link(self, obj):
        return obj.get_absolute_url()

    def description(self, obj):
        return "Medias recently registered under tag %s" % obj.name

    def items(self, obj):
        photos = obj.photo_set.order_by('-timestamp')[:15]
        videos = obj.video_set.order_by('-time_created')[:15]
        medias = list(photos) + list(videos)
        medias.sort()
        medias.reverse()
        return medias[:15]

class Comments(Feed):
    title = "Recent comments"
    link = "/gallery/"
    description = "Comments recently added"

    def items(self):
        return Comment.objects.filter(public=True).order_by('-submit_date')[:15]
