from django.db import models

class PhotoAddon(models.Model):
    photo_id = models.IntegerField(null=True, blank=True)
    hits = models.IntegerField(default=0)


class VideoAddon(models.Model):
    video_id = models.IntegerField(null=True, blank=True)
    hits = models.IntegerField(default=0)

class TagAddon(models.Model):
    tag_id = models.IntegerField()
    description = models.CharField(max_length=350)

    class Admin:
        pass
