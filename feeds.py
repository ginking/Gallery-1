from django.contrib.syndication.feeds import Feed
from gallery.models import Tag, OriginalExport, Comment
from django.core.exceptions import ObjectDoesNotExist

class Photos(Feed):
    title = "Chicagocrime.org site news"
    link = "/sitenews/"
    description = "Updates on changes and additions to chicagocrime.org."

    def items(self):
        photos = OriginalExport.get_random(15)
        #items = [ {'title': p.title, 'description': '<img src="%s"'
        return []

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
        return Comment.objects.order_by('-time')[:15]

    
