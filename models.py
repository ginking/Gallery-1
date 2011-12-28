from django.db import models, connection
from django.conf import settings
from django.template.defaultfilters import slugify
from django.contrib.sites.models import Site

import datetime
import time
import os, Image
import EXIF

from addon_models import PhotoAddon, VideoAddon, TagAddon

G_URL=settings.GALLERY_SETTINGS['rel_url']
G_PORT=settings.GALLERY_SETTINGS.get('port')
SITE=Site.objects.get_current()

if G_PORT:
    SITE_URL = 'http://%s:%s%s' % (SITE, G_PORT, G_URL)
else:
    SITE_URL = 'http://%s%s' % (SITE, G_URL)

def shotwell_photo_id_to_db_id(weird_id):
    # thumb00000000000x -> base10 number
    return int("0x%s" % weird_id[5:], 16)

def db_id_to_shotwell_photo_id(normal_id):
    # base10 number -> thumb00000000000x
    hex_id = hex(normal_id)[2:]
    return 'thumb' + (16 - len(hex_id)) * '0' + hex_id

def shotwell_video_id_to_db_id(weird_id):
    # video-0000000000000013 -> base10 number
    return int("0x%s" % weird_id[6:], 16)

def db_id_to_shotwell_video_id(normal_id):
    # base10 number -> video-0000000000000013
    hex_id = hex(normal_id)[2:]
    return 'video-' + (16 - len(hex_id)) * '0' + hex_id

class OriginalExport(models.Model):
    id = models.IntegerField(primary_key=True)
    normal_relpath = models.TextField()
    thumb_relpath = models.TextField()
    mq_relpath = models.TextField()
    hq_relpath = models.TextField()

    media_url = '%s/media/' % SITE_URL

    photo = models.ForeignKey("Photo", db_column="id")
    timestamp_spec = "photo__timestamp"

    class Meta:
        db_table = 'original_exports'

    def __str__(self):
        return self.normal_relpath

    def as_dict(self):
        return {'thumb_url': self.thumb_url(),
                'normal_url': self.normal_url(),
                'hq_url': self.hq_url(),
                'mq_url': self.mq_url()}

    def perm_url(self):
        return "%s/photo/%s" % (G_URL, self.id)

    get_absolute_url = perm_url

    def normal_width(self):
        # FIXME: store in db
        return self.get_normal_size()[0]

    def normal_height(self):
        # FIXME: store in db
        return self.get_normal_size()[1]

    def get_normal_size(self):
        if not hasattr(self, "_size"):
            media_path = settings.GALLERY_SETTINGS.get('media_path')
            full_path = open(os.path.join(media_path, self.normal_relpath))
            i = Image.open(full_path)
            self._size = i.size
        return self._size

    def thumb_url(self):
        return "%s%s" % (self.media_url, self.thumb_relpath)

    def normal_url(self):
        return "%s%s" % (self.media_url, self.normal_relpath)

    def hq_url(self):
        url = ""
        if self.hq_relpath:
            url = "%s%s" % (self.media_url, self.hq_relpath)
        return url

    def mq_url(self):
        url = ""
        if self.mq_relpath:
            url = "%s%s" % (self.media_url, self.mq_relpath)
        return url


class OriginalVideoExport(models.Model):
    id = models.IntegerField(primary_key=True)
    thumbnail_path = models.TextField()
    webm_video_path = models.TextField()
    webm_video_width = models.IntegerField()
    webm_video_height = models.IntegerField()

    video = models.ForeignKey("Video", db_column="id")
    timestamp_spec = "video__time_created"

    class Meta:
        db_table = u'original_video_export'

    media_url = '%s/media/' % SITE_URL

    def normal_width(self):
        return self.webm_video_width

    def normal_height(self):
        return self.webm_video_height

    def thumb_url(self):
        return "%s%s" % (self.media_url, self.thumbnail_path)

    def normal_url(self):
        return "%s%s" % (self.media_url, self.webm_video_path)

    def perm_url(self):
        return "%s/video/%s" % (G_URL, self.id)

    get_absolute_url = perm_url

class Event(models.Model):
    id = models.IntegerField(null=True, primary_key=True, blank=True)
    name = models.TextField(blank=True)
    primary_photo_id = models.IntegerField(null=True, blank=True)
    time_created = models.IntegerField(null=True, blank=True)
    primary_source_id = models.TextField(blank=True)

    class Meta:
        db_table = u'EventTable'

    @property
    def primary_photo(self):
        return Photo.objects.using("gallery").get(shotwell_photo_id_to_db_id(self.primary_photo_id))

    @property
    def url(self):
        return '%s/event/%s/' % (G_URL, self.id)

    @property
    def timestamp(self):
        if not hasattr(self, '_timestamp'):
            try:
                self._timestamp = self.photo_set.order_by('timestamp')[0].timestamp
            except IndexError:
                self._timestamp = self.video_set.order_by('time_created')[0].time_created
        return self._timestamp

    def date(self):
        return datetime.date.fromtimestamp(self.timestamp)

    def time(self):
        return datetime.datetime.fromtimestamp(self.timestamp)

    @property
    def tags(self):
        tags = []
        for photo in self.photo_set.all():
            for tag in photo.get_tags():
                if tag not in tags:
                    tags.append(tag)
        tags.sort()
        return tags

class Media(object):

    @classmethod
    def get_random(cls, number, since=None):
        objects = cls.ExportClass.objects.using("gallery")
        if since:
            timestamp_match = "%s__gt" % cls.ExportClass.timestamp_spec
            condition = {timestamp_match: float(since)}
            objects = objects.filter(**condition)
        return objects.order_by('?')[:number]

    @classmethod
    def recent(cls):
        t = settings.GALLERY_SETTINGS['recent_photos_time']
        date = int(time.time() - t)
        if cls == Photo:
            condition = {'timestamp__gt': date}
        else:
            condition = {'time_created__gt': date}
        return cls.objects.using("gallery").filter(**condition).distinct()

    def get_sibling_media(self, direction, tag=None, event_id=None):
        media = None
        event = None

        if tag:
            photo_set = tag.photo_set
            video_set = tag.video_set
        elif event_id:
            event = Event.objects.using("gallery").get(id=event_id)
            photo_set = event.photo_set
            video_set = event.video_set
        else:
            return None

        timestamp = self.timestamp
        if direction == 'previous':
            photos = photo_set.filter(timestamp__lt=timestamp).order_by('-timestamp')
            videos = video_set.filter(time_created__lt=timestamp).order_by('-time_created')
            idx = 1
        else:
            photos = photo_set.filter(timestamp__gt=timestamp).order_by('timestamp')
            videos = video_set.filter(time_created__gt=timestamp).order_by('time_created')
            idx = 0

        medias = []
        if photos:
            medias.append(photos[0])
        if videos:
            medias.append(videos[0])

        if medias:
            medias.sort()
            try:
                media = medias[idx]
            except IndexError:
                media = medias[0]
            if tag:
                media._url = media.url(slugify(tag.name))
            else:
                media._url = media.url(event_id)
        return media

    def __cmp__(self, other_media):
        return cmp(self.timestamp, other_media.timestamp)

    def event_url(self):
        return '%s/event/%s/%s/%s' % (G_URL, self._media_type(), self.id, self.event.id)

    def same_day_url(self):
        day = datetime.date.fromtimestamp(self.timestamp)
        return '%s/date/%s/%s/%s' % (G_URL, day.year, day.month, day.day)

    def get_date(self):
        day = datetime.date.fromtimestamp(self.timestamp)
        d = datetime.date(day.year, day.month, day.day)
        human_date = d.strftime('%A %d %B')
        return human_date

    @classmethod
    def for_date(cls, year, month, day):
        one_day = datetime.timedelta(hours=23, minutes=59, seconds=59)
        the_day = datetime.datetime(year=year, month=month, day=day)
        midnight = the_day + one_day
        r = (int(time.mktime(the_day.timetuple())),
             int(time.mktime(midnight.timetuple())))
        objects = cls.objects.using("gallery")
        if cls == Photo:
            medias = objects.exclude(timestamp__gte=r[1]).filter(timestamp__gte=r[0]).order_by('timestamp')
        else:
            medias = objects.exclude(time_created__gte=r[1]).filter(time_created__gte=r[0]).order_by('time_created')
        return medias

    def _media_type(self):
        if isinstance(self, Video):
            return "video"
        else:
            return "photo"

    def _foreign_key_name(self):
        return "%s_id" % self._media_type()

    def get_hits(self):
        cond = {self._foreign_key_name(): self.id}
        try:
            addon = self.AddonClass.objects.get(**cond)
        except:
            hits = 0
        else:
            hits = addon.hits
        return hits

    def increment_hit(self):
        cond = {self._foreign_key_name(): self.id}
        try:
            addon = self.AddonClass.objects.get(**cond)
        except:
            cond["hits"] = 1
            addon = self.AddonClass(**cond)
        else:
            addon.hits += 1
        addon.save()

    def get_exported(self):
        if not hasattr(self, '_exported'):
            self._exported = self.ExportClass.objects.using("gallery").get(id=self.id)
        return self._exported

    def get_tags(self, recurse=True):
        all_tags = {}
        for tag in self.tags.all():
            if not tag.is_category:
                all_tags[tag.name] = tag
        return all_tags.values()

    def get_comments(self):
        if isinstance(self, Photo):
            condition = {"photo_id": self.id}
        else:
            condition = {"video_id": self.id}
        comments = Comment.objects.filter(**condition).order_by('submit_date')
        if not comments:
            comments = []
        return comments

class Photo(models.Model, Media):
    id = models.IntegerField(null=True, primary_key=True, blank=True)
    filename = models.TextField(unique=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    filesize = models.IntegerField(null=True, blank=True)
    timestamp = models.IntegerField(null=True, blank=True)
    exposure_time = models.IntegerField(null=True, blank=True)
    orientation = models.IntegerField(null=True, blank=True)
    original_orientation = models.IntegerField(null=True, blank=True)
    import_id = models.IntegerField(null=True, blank=True)
    transformations = models.TextField(blank=True)
    md5 = models.TextField(blank=True)
    thumbnail_md5 = models.TextField(blank=True)
    exif_md5 = models.TextField(blank=True)
    time_created = models.IntegerField(null=True, blank=True)
    flags = models.IntegerField(null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True)
    file_format = models.IntegerField(null=True, blank=True)
    title = models.TextField(blank=True)
    backlinks = models.TextField(blank=True)
    time_reimported = models.IntegerField(null=True, blank=True)
    editable_id = models.IntegerField(null=True, blank=True)
    metadata_dirty = models.IntegerField(null=True, blank=True)
    developer = models.TextField(blank=True)
    develop_shotwell_id = models.IntegerField(null=True, blank=True)
    develop_camera_id = models.IntegerField(null=True, blank=True)
    develop_embedded_id = models.IntegerField(null=True, blank=True)
    event = models.ForeignKey(Event)

    class Meta:
        db_table = u'PhotoTable'

    AddonClass = PhotoAddon
    ExportClass = OriginalExport

    def __str__(self):
        return self.title or self.name

    @property
    def name(self):
        return self.filename

    def as_dict(self):
        return {'id': self.id, 'time': self.timestamp,
                'name': self.name,
                'pictures': self.get_exported().as_dict(),
                'description': self.title,
                'exif': [i for i in self.get_exif_infos() if i != ' | '],
                'comments': [ c.as_dict() for c in self.get_comments()],
                'tags': [tag.name for tag in self.get_tags()]}

    @property
    def shotwell_photo_id(self):
        return db_id_to_shotwell_photo_id(self.id)

    @property
    def tags(self):
        return Tag.objects.using("gallery").filter(photo_id_list__contains=self.shotwell_photo_id)

    def url(self, extra=None):
        if hasattr(self, '_url'):
            return self._url

        url = '%s/photo/%s/' % (G_URL, self.id)
        if extra:
            if extra.startswith('/'):
                extra = extra[1:]
            url += extra
        return url

    get_absolute_url = url

    def in_tag_url(self, tag_name):
        return '%s/photo/%s/%s' % (G_URL, self.id, slugify(tag_name))

    @property
    def exif_data(self):
        if not hasattr(self, "_exif"):
            media_path = settings.GALLERY_SETTINGS.get('media_path')
            ex = self.get_exported()
            f = open(os.path.join(media_path, ex.normal_relpath))
            self._exif = EXIF.process_file(f)
            f.close()
        return self._exif

    def get_exif_infos(self):
        data = self.exif_data

        infos = []
        for k, v in (('EXIF DateTimeOriginal', 'Time Taken'),
                     ('Image Make', 'Camera Manufacturer'),
                     ('Image Model', 'Camera Model'),
                     ('EXIF FocalLength', 'Real Focal Length'),
                     ('FIXME what here?', 'Focal Length Relative to 35mm Film'),
                     ('EXIF FNumber', 'F Stop'),
                     ('EXIF ExposureTime', 'Time of Exposure'),
                     ('EXIF Flash', 'Flash')):
            if k in data:
##                 if len(infos) > 1:
##                     infos.append(' | ')
                infos.append({'title': v, 'value': str(data[k])})

        return infos


class Tag(models.Model):
    id = models.IntegerField(null=True, primary_key=True, blank=True)
    name = models.TextField(unique=True)
    photo_id_list = models.TextField(blank=True)
    time_created = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = u'TagTable'

    class Admin:
        fields = (
            (None, {
            'fields': ('id', 'name',)
            }),
            #('Advanced options', {
            #'classes': 'collapse',
            #'fields' : ('enable_comments', 'registration_required', 'template_name')
            #}),
            )
        list_display = ('name', 'get_description',)

    @property
    def is_category(self):
        return len(self.name.split("/")) == 2

    @property
    def photo_set(self):
        # example of photo_id_list value: thumb0000000000000011,thumb0000000000000013,
        real_photo_ids = [ shotwell_photo_id_to_db_id(weird_id)
                           for weird_id in self.photo_id_list.split(",")
                           if weird_id.startswith("thumb")]
        return Photo.objects.using("gallery").filter(id__in=real_photo_ids)

    @property
    def video_set(self):
        # example of photo_id_list value: video-0000000000000011,video-0000000000000013,
        real_video_ids = [ shotwell_video_id_to_db_id(weird_id)
                           for weird_id in self.photo_id_list.split(",")
                           if weird_id.startswith("video")]
        return Video.objects.using("gallery").filter(id__in=real_video_ids)

    @property
    def human_name(self):
        return self.name.split("/")[-1]

    def __str__(self):
        desc = self.get_description()
        if desc:
            s = "%s: %s" % (self.name, desc)
        else:
            s = self.name
        return s

    def as_dict(self):
        return {'id': self.id, 'name': self.name,
                'description': self.get_description(),
                #'photo_count': self.photo_set.count()
                }

    @classmethod
    def build_set(cls, tag_combination):
        tag_names = tag_combination.split('+')
        tags = [ t for t in list(Tag.objects.using("gallery").all())
                 if slugify(t.name) in tag_names ]
        final_set = []
        for tag in tags:
            final_set.extend(tag.photo_set.all())
            final_set.extend(tag.video_set.all())
        return final_set

    @classmethod
    def with_name(cls, slugified):
        tags = [ t for t in list(Tag.objects.using("gallery").all())
                 if slugify(t.name) == slugified ]
        if tags:
            tag = tags[0]
        else:
            tag = None
        return tag

    @classmethod
    def get_cloud(cls):
        words = [(t.name, t.human_name, t.photo_set.count() + t.video_set.count())
                 for t in cls.objects.using("gallery").all() if not t.is_category]
        words.sort()
        return cls._get_cloud(words)

    @classmethod
    def _get_cloud(cls, entries):
        ''' distribution algo n tags to b bucket, where b represents
        font size. '''
        cloud = []

        class _Tag:

            def __init__(self, name, human_name, count):
                self.name = human_name
                self.shotwell_name = name
                self.count = count

            def __cmp__(self, other):
                return cmp(self.count, other.count)

            def __repr__(self):
                return "<tag: %s : %s>" % (self.name, self.count)
        
        tag_list = []
        for name, human_name, count in entries:
            tag = _Tag(name, human_name, count)
            tag_list.append(tag)
        
        nbr_of_buckets = 8
        base_font_size = 16
        tresholds = []
        max_tag = max(tag_list)
        min_tag = min(tag_list)
        delta = (float(max_tag.count) -
                 float(min_tag.count)) / (float(nbr_of_buckets))
        # set a treshold for all buckets
        for i in range(nbr_of_buckets):
            tresh_value =  float(min_tag.count) + (i+1) * delta
            tresholds.append(tresh_value)
        # set font size for tags (per bucket)
        for tag in tag_list:
            font_set_flag = False
            for bucket in range(nbr_of_buckets):
                if font_set_flag == False:
                    if (tag.count <= tresholds[bucket]):
                        font_size = base_font_size + (bucket * 2)
                        font_set_flag = True
                        url = '%s/tag/%s' % (G_URL, slugify(tag.shotwell_name))
                        cloud.append({'size': font_size, 'url': url,
                                      'name': tag.name})
        return cloud

    @classmethod
    def get_recent_tags_cloud(cls):
        t = settings.GALLERY_SETTINGS['recent_photos_time']
        date = int(time.time() - t)
        tags = []
        for tag in cls.objects.using("gallery").all():
            if tag.is_category:
                continue
            recent_photos = tag.photo_set.filter(timestamp__gt=date).distinct()
            recent_videos = tag.video_set.filter(time_created__gt=date).distinct()
            if recent_photos or recent_videos:
                tags.append(tag)

        return tags

    def get_recent_photos(self):
        t = settings.GALLERY_SETTINGS['recent_photos_time']
        date = int(time.time() - t)
        return self.photo_set.filter(timestamp__gt=date).distinct()

    def get_recent_videos(self):
        t = settings.GALLERY_SETTINGS['recent_photos_time']
        date = int(time.time() - t)
        return self.video_set.filter(time_created__gt=date).distinct()

    def url(self):
        return '%s/tag/%s' % (G_URL, slugify(self.name))

    get_absolute_url = url

    def recent_url(self):
        return '%s/recent/%s' % (G_URL, slugify(self.name))

    def get_description(self):
        try:
            addon = TagAddon.objects.get(tag_id=self.id)
        except:
            description = ''
        else:
            description = addon.description
        return description

    def set_description(self, desc):
        try:
            addon = TagAddon.objects.get(tag_id=self.id)
        except:
            addon = TagAddon(tag_id=self.id, description=desc)
        else:
            addon.description = desc
        addon.save()

    def get_tags(self):
        if not self.is_category:
            return []
        return Tag.objects.using("gallery").filter(name__in=self.name)

class Video(models.Model, Media):
    id = models.IntegerField(null=True, primary_key=True, blank=True)
    filename = models.TextField(unique=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    clip_duration = models.FloatField(null=True, blank=True)
    is_interpretable = models.IntegerField(null=True, blank=True)
    filesize = models.IntegerField(null=True, blank=True)
    timestamp = models.IntegerField(null=True, blank=True)
    exposure_time = models.IntegerField(null=True, blank=True)
    import_id = models.IntegerField(null=True, blank=True)
    md5 = models.TextField(blank=True)
    time_created = models.IntegerField(null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True)
    title = models.TextField(blank=True)
    backlinks = models.TextField(blank=True)
    time_reimported = models.IntegerField(null=True, blank=True)
    flags = models.IntegerField(null=True, blank=True)
    event = models.ForeignKey(Event)

    AddonClass = VideoAddon
    ExportClass = OriginalVideoExport

    class Meta:
        db_table = u'VideoTable'

    @property
    def shotwell_video_id(self):
        return db_id_to_shotwell_video_id(self.id)

    @property
    def timestamp(self):
        return self.time_created

    @property
    def tags(self):
        return Tag.objects.using("gallery").filter(photo_id_list__contains=self.shotwell_video_id)

    def url(self, extra=None):
        if hasattr(self, '_url'):
            return self._url

        url = '%s/video/%s/' % (G_URL, self.id)
        if extra:
            if extra.startswith('/'):
                extra = extra[1:]
            url += extra
        return url

    get_absolute_url = url


class Comment(models.Model):
    photo_id = models.IntegerField(null=True)
    video_id = models.IntegerField(null=True)
    comment = models.TextField()
    author = models.CharField(max_length=60)
    website = models.CharField(max_length=128, blank=True)
    submit_date = models.DateTimeField(blank=True)
    is_openid = models.BooleanField(default=True)
    public = models.BooleanField(default=True)

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

    @property
    def photo(self):
        return Photo.objects.using("gallery").get(id=self.photo_id)

    @property
    def video(self):
        return Video.objects.using("gallery").get(id=self.video_id)
