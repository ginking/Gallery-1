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

class Comment(models.Model):
    comment = models.TextField()
    author = models.CharField(max_length=60)
    website = models.CharField(max_length=128, blank=True)
    submit_date = models.DateTimeField(blank=True)
    is_openid = models.BooleanField(default=True)
    public = models.BooleanField(default=True)

    photo = models.ForeignKey("Photo")
    video = models.ForeignKey("Video")

    class Admin:
        list_display = ('id','public','photo', 'comment', 'submit_date',)

    class Meta:
        ordering = ('-submit_date',)

    def __str__(self):
        if self.photo_id:
            return "%s on photo %s: %s..." % (self.author, self.photo_id,
                                              self.comment[:100])
        else:
            return "%s on video %s: %s..." % (self.author, self.video_id,
                                              self.comment[:100])

    def as_dict(self):
        return {'comment': self.comment, 'author': self.author,
                'website': self.website, 'submit_date': self.submit_date}

    def url(self):
        if self.photo_id:
            return '%s#c%s' % (self.photo.url(), self.id)
        else:
            return '%s#c%s' % (self.video.url(), self.id)

    get_absolute_url = url
