from django.contrib.syndication.feeds import Feed
from gallery.models import Tag, OriginalExport

class LatestPhotos(Feed):
    title = "Chicagocrime.org site news"
    link = "/sitenews/"
    description = "Updates on changes and additions to chicagocrime.org."

    def items(self):
        photos = OriginalExport.get_random(15)
        #items = [ {'title': p.title, 'description': '<img src="%s"'
        return []

class LatestPhotosByTag(Feed):
    title = "Photos by tag"
    link = "/gallery/"
    description = "Foo"

    def items(self):
        return Tag.get_recent_tags_cloud()
