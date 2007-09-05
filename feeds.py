from django.contrib.syndication.feeds import Feed
from gallery.models import Tag, Photo, Comment
from django.core.exceptions import ObjectDoesNotExist

class Photos(Feed):
    title = "Photos recently added"
    link = "/gallery/"
    description = title

    def items(self):
        return Photo.objects.order_by('-time')[:15]

class Tags(Feed):
    title = "Tags recently updated"
    link = "/gallery/"
    description = "Tags recently updated"

    def items(self):
        return Tag.get_recent_tags_cloud()

class PhotosByTag(Feed):
    
    def get_object(self, bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return Tag.with_name(bits[0])

    def title(self, obj):
        return "Photos tagged with %s" % obj.name

    def link(self, obj):
        return obj.get_absolute_url()

    def description(self, obj):
        return "Photos recently registered under tag %s" % obj.name

    def items(self, obj):
        return obj.photo_set.order_by('-time')[:15]

class Comments(Feed):
    title = "Recent comments"
    link = "/gallery/"
    description = "Comments recently added"

    def items(self):
        return Comment.objects.filter(public__eq=True).order_by('-submit_date')[:15]
