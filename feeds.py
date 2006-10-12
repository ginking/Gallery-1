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

class LatestTags(Feed):
    title = "Tags recently updated"
    link = "/gallery/"
    description = "Tags recently updated"

    def items(self):
        return Tag.get_recent_tags_cloud()

class LatestPhotosByTag(Feed):
    pass
