from django.db import models, connection, connections
from django.conf import settings
from django.template.defaultfilters import slugify
from django.contrib.sites.models import Site

import datetime
import time
import os, Image
import EXIF

G_URL=settings.GALLERY_SETTINGS['rel_url']
G_PORT=settings.GALLERY_SETTINGS.get('port')
SITE=Site.objects.get_current()

if G_PORT:
    SITE_URL = 'http://%s:%s%s' % (SITE, G_PORT, G_URL)
else:
    SITE_URL = 'http://%s%s' % (SITE, G_URL)

def shotwell_id_to_db_id(weird_id):
    # thumb00000000000x -> base10 number
    return int("0x%s" % weird_id[5:], 16)

def db_id_to_shotwell_id(normal_id):
    # base10 number -> thumb00000000000x
    hex_id = hex(normal_id)[2:]
    return 'thumb' + (16 - len(hex_id)) * '0' + hex_id

class OriginalExport(models.Model):
    id = models.IntegerField(primary_key=True)
    normal_relpath = models.TextField()
    thumb_relpath = models.TextField()
    mq_relpath = models.TextField()
    hq_relpath = models.TextField()

    media_url = '%s/media/' % SITE_URL

    class Meta:
        db_table = 'original_exports'

    def __str__(self):
        return self.normal_relpath

    def as_dict(self):
        return {'thumb_url': self.thumb_url(),
                'normal_url': self.normal_url(),
                'hq_url': self.hq_url(),
                'mq_url': self.mq_url()}

    @classmethod
    def get_random(cls, number, since=None, category_id=None):
        cls_objects = cls.objects.using("gallery")
        if not since and not category_id:
            objects = cls_objects.order_by('?')[:number]
        elif since:
            sql = 'select oe.id from original_exports oe, PhotoTable p where oe.id=p.id and p.timestamp > %r order by random() limit %r'
            cursor = connections["gallery"].cursor()
            cursor.execute(sql % (float(since), int(number),))
            objects = [cls_objects.get(id=id) for [id,] in cursor.fetchall()]
        elif category_id:
            sql = 'select oe.id from original_exports oe, photo_tags pt where oe.id=pt.photo_id and pt.tag_id in (select id from tags where category_id=%r) order by random() limit %r'
            cursor = connections["gallery"].cursor()
            cursor.execute(sql % (category_id, number,))
            objects = [cls_objects.get(id=id) for [id,] in cursor.fetchall()]

        return objects

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
        return Photo.objects.using("gallery").get(shotwell_id_to_db_id(self.primary_photo_id))

    @property
    def url(self):
        return '%s/event/%s/' % (G_URL, self.id)

    @property
    def timestamp(self):
        if not hasattr(self, '_timestamp'):
            self._timestamp = self.photo_set.order_by('timestamp')[0].timestamp
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

class Photo(models.Model):
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

    @classmethod
    def for_date(self, year, month, day):
        one_day = datetime.timedelta(hours=23, minutes=59, seconds=59)
        the_day = datetime.datetime(year=year, month=month, day=day)
        midnight = the_day + one_day
        r = (int(time.mktime(the_day.timetuple())),
             int(time.mktime(midnight.timetuple())))
        photos = self.objects.using("gallery").exclude(timestamp__gte=r[1]).filter(timestamp__gte=r[0])
        photos = photos.order_by('timestamp')
        return photos

    @classmethod
    def popular(cls, tag_name):
        photos = []
        # Take at most 10 photos having their hits number > 20
        max_photos = 10
        min_hits = 20
        most_viewed = PhotoAddon.objects.exclude(hits__lte=min_hits).order_by('-hits')
        if not tag_name:
            most_viewed = most_viewed[:max_photos]

        for addon in most_viewed:
            try:
                photo = cls.objects.using("gallery").get(id=addon.photo_id)
            except:
                continue
            if tag_name:
                tags = [ slugify(t.name) for t in photo.get_tags(recurse=False) ]
                if tag_name not in tags:
                    continue
            if len(photos) > max_photos:
                break
            photo.hits = addon.hits
            photos.append(photo)
        return photos

    @classmethod
    def recent(cls):
        t = settings.GALLERY_SETTINGS['recent_photos_time']
        date = int(time.time() - t)
        photos = cls.objects.using("gallery").filter(timestamp__gt=date).distinct()
        return photos

    @property
    def shotwell_photo_id(self):
        return db_id_to_shotwell_id(self.id)

    @property
    def tags(self):
        return Tag.objects.using("gallery").filter(photo_id_list__contains=self.shotwell_photo_id)

    def get_tags(self, recurse=True):
        all_tags = {}
        for tag in self.tags.all():
            if not tag.is_category:
                all_tags[tag.name] = tag
        return all_tags.values()

    def get_comments(self):
        comments = Comment.objects.filter(photo_id=self.id).order_by('submit_date')
        if not comments:
            comments = []
        return comments

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

    def same_day_url(self):
        day = datetime.date.fromtimestamp(self.timestamp)
        return '%s/date/%s/%s/%s' % (G_URL, day.year, day.month, day.day)

    def get_exported(self):
        if not hasattr(self, '_exported'):
            self._exported = OriginalExport.objects.using("gallery").get(id=self.id)
        return self._exported

    def get_hits(self):
        try:
            addon = PhotoAddon.objects.get(photo_id=self.id)
        except:
            hits = 0
        else:
            hits = addon.hits
        return hits

    def get_date(self):
        day = datetime.date.fromtimestamp(self.timestamp)
        d = datetime.date(day.year, day.month, day.day)
        human_date = d.strftime('%A %d %B')
        return human_date

    def increment_hit(self):
        try:
            addon = PhotoAddon.objects.get(photo_id=self.id)
        except:
            addon = PhotoAddon(photo_id=self.id, hits=1)
        else:
            addon.hits += 1
        addon.save()

    def get_sibling_photo(self, direction, tag=None, event_id=None):
        photo = None
        prev = direction == 'previous'
        if tag:
            if prev:
                photos = tag.photo_set.filter(timestamp__lt=self.timestamp).order_by('-timestamp')
            else:
                photos = tag.photo_set.filter(timestamp__gt=self.timestamp).order_by('timestamp')
            if photos:
                photo = photos[0]
                photo._url = photo.url(slugify(tag.name))
        elif event_id:
            event = Event.objects.using("gallery").get(id=event_id)
            if prev:
                photos = event.photo_set.filter(timestamp__lt=self.timestamp).order_by('-timestamp')
            else:
                photos = event.photo_set.filter(timestamp__gt=self.timestamp).order_by('timestamp')
            if photos:
                photo = photos[0]
                photo._url = photo.url(event_id)
        return photo

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
        real_photo_ids = [ shotwell_id_to_db_id(weird_id)
                           for weird_id in self.photo_id_list.split(",") if weird_id]
        return Photo.objects.using("gallery").filter(id__in=real_photo_ids)

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
        words = [(t.name, t.human_name, t.photo_set.count()) for t in cls.objects.using("gallery").all()
                 if not t.is_category]
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
            recent_photos = tag.photo_set.filter(timestamp__gt=date).distinct()
            if recent_photos and not tag.is_category:
                tags.append(tag)

        return tags

    def get_recent_photos(self):
        t = settings.GALLERY_SETTINGS['recent_photos_time']
        date = int(time.time() - t)
        photos = self.photo_set.filter(timestamp__gt=date).distinct()
        return photos

    def url(self):
        return '%s/tag/%s' % (G_URL, slugify(self.name))

    get_absolute_url = url

    def recent_url(self):
        return '%s/recent/%s' % (G_URL, slugify(self.name))

    def popular_url(self):
        return '%s/popular/%s' % (G_URL, slugify(self.name))

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

class TagAddon(models.Model):
    tag_id = models.IntegerField()
    description = models.CharField(max_length=350)

    class Admin:
        pass

class PhotoAddon(models.Model):
    photo_id = models.IntegerField(null=True, blank=True)
    hits = models.IntegerField(default=0)

class Comment(models.Model):
    photo_id = models.IntegerField(null=True, blank=True)
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
        return "%s on photo %s: %s..." % (self.author, self.photo_id,
                                          self.comment[:100])

    def as_dict(self):
        return {'comment': self.comment, 'author': self.author,
                'website': self.website, 'submit_date': self.submit_date}

    def url(self):
        return '%s#c%s' % (self.photo().url(), self.id)

    get_absolute_url = url

    def photo(self):
        return Photo.objects.using("gallery").get(id=self.photo_id)
