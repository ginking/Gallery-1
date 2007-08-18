# Also note: You'll have to insert the output of 'django-admin.py sqlinitialdata [appname]'
# into your database.

from django.db import models, connection, connections
from django.conf import settings
from django.template.defaultfilters import slugify
from django.contrib.sites.models import Site

import datetime
import time
import os, Image
import EXIF

G_URL=settings.GALLERY_SETTINGS['rel_url']
SITE=Site.objects.get_current()

## class Import(models.Model):
##     id = models.IntegerField(primary_key=True)
##     time = models.IntegerField(null=True, blank=True)
##     class Meta:
##         db_table = 'imports'

## class Meta(models.Model):
##     id = models.IntegerField(primary_key=True)
##     name = models.TextField(unique=True)
##     data = models.TextField(blank=True)
##     class Meta:
##         db_table = 'meta'

class OriginalExport(models.Model):
    id = models.IntegerField(primary_key=True)
    normal_relpath = models.TextField() # This field type is a guess.
    thumb_relpath = models.TextField() # This field type is a guess.
    mq_relpath = models.TextField() # This field type is a guess.
    hq_relpath = models.TextField() # This field type is a guess.

    media_url = 'http://%s%s/media/' % (SITE, G_URL)
    
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
        if not since and not category_id:
            objects = cls.objects.order_by('?')[:number]
        elif since:
            sql = 'select oe.id from original_exports oe, photos p where oe.id=p.id and p.time > %r order by random() limit %r'
            
            connection = OriginalExport.objects.db.connection
            cursor = connection.cursor()
            cursor.execute(sql % (float(since), int(number),))
            objects = [cls.objects.get(id=id) for [id,] in cursor.fetchall()]
        elif category_id:
            sql = 'select oe.id from original_exports oe, photo_tags pt where oe.id=pt.photo_id and pt.tag_id in (select id from tags where category_id=%r) order by random() limit %r'
            connection = OriginalExport.objects.db.connection
            cursor = connection.cursor()
            cursor.execute(sql % (category_id, number,))
            objects = [cls.objects.get(id=id) for [id,] in cursor.fetchall()]
            
        return objects

    def perm_url(self):
        return "%s/photo/%s" % (G_URL, self.id)

    get_absolute_url = perm_url

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
        

## class PhotoTag(models.Model):
##     #photo_id = models.IntegerField(null=True, blank=True)
##     photo = models.ForeignKey('Photo')
##     #tag_id = models.IntegerField(null=True, blank=True)
##     tag = models.ForeignKey('Tag')
##     class Meta:
##         db_table = 'photo_tags'

## class PhotoVersion(models.Model):
##     photo_id = models.IntegerField(null=True, blank=True)
##     version_id = models.IntegerField(primary_key=True)
##     name = models.TextField(blank=True) # This field type is a guess.
##     class Meta:
##         db_table = 'photo_versions'

class PhotoTags(models.ManyToManyField):

    def __init__(self):
        models.ManyToManyField.__init__(self, 'Tag')
    
    def _get_m2m_db_table(self, opts):
        return 'photo_tags'
    
class Photo(models.Model):
    id = models.IntegerField(primary_key=True)
    time = models.IntegerField()
    directory_path = models.TextField() # This field type is a guess.
    name = models.TextField() # This field type is a guess.
    description = models.TextField()
    default_version_id = models.IntegerField()
    tags = PhotoTags()
    
    class Meta:
        db_table = 'photos'

    def __str__(self):
        if self.description:
            desc = self.description
        else:
            desc = self.name
        return desc

    def as_dict(self):
        return {'id': self.id, 'time': self.time,
                'name': self.name,
                'pictures': self.get_exported().as_dict(),
                'description': self.description,
                'exif': [i for i in self.get_exif_infos() if i != ' | '],
                'comments': [ c.as_dict() for c in self.get_comments()],
                'tags': [tag.name for tag in self.get_tags()]}#self.tags.all()]}

        
    @classmethod
    def for_date(self, year, month, day):
        one_day = datetime.timedelta(hours=23, minutes=59, seconds=59)
        the_day = datetime.datetime(year=year, month=month, day=day)
        midnight = the_day + one_day
        r = (int(time.mktime(the_day.timetuple())),
             int(time.mktime(midnight.timetuple())))
        photos = self.objects.exclude(time__gte=r[1]).filter(time__gte=r[0])
        photos = photos.order_by('time')
        return photos


    def get_tags(self):
        all_tags = {}
        for tag in self.tags.all():
            all_tags[tag.name] = tag
            #
            try:
                parent_tag = Tag.objects.get(id=tag.category_id)
            except:
                continue
            all_tags[parent_tag.name] = parent_tag
            #import pdb; pdb.set_trace()
            while 1:
                try:
                    parent_tag = Tag.objects.get(id=parent_tag.category_id)
                except:
                    break
                if parent_tag.photo_set.all():
                    all_tags[parent_tag.name] = parent_tag
        
        return all_tags.values()

    def get_comments(self):
        comments = Comment.objects.filter(photo_id=self.id)
        if not comments:
            comments = []
        return comments

    def url(self, extra=None):
        if hasattr(self, '_url'):
            return self._url

        #url = 'http://%s%s/photo/%s' % (SITE, G_URL, self.id)
        url = '%s/photo/%s/' % (G_URL, self.id)
        if extra:
            if not extra.startswith('/'):
                extra = '/' + extra
            url += extra
        return url

    get_absolute_url = url

    def in_tag_url(self, tag_name):
        return '%s/photo/%s/%s' % (G_URL, self.id, slugify(tag_name))

    def same_day_url(self):
        day = datetime.date.fromtimestamp(self.time)
        return '%s/date/%s/%s/%s' % (G_URL, day.year, day.month, day.day)

    def get_exported(self):
        if not hasattr(self, '_exported'):
            self._exported = OriginalExport.objects.get(id=self.id)
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
        day = datetime.date.fromtimestamp(self.time)
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
        
    def get_sibling_photo(self, direction, tag):
        photo = None
        if tag:
            prev = direction == 'previous'
            sql = ('select pt.photo_id from '
                   '       tags t, photo_tags pt'
                   '       where t.id=pt.tag_id'
                   '       and t.name="%%s" and pt.photo_id %s %%d '
                   '       order by pt.photo_id %s limit 1'
                   % (prev and '<' or '>', prev and 'desc' or 'asc'))
            
            connection = Photo.objects.db.connection
            cur = connection.cursor()
            cur.execute(sql % (tag.name, int(self.id)))
            res = cur.fetchone()
            if res:
                photo = Photo.objects.get(id=res[0])
                photo._url = photo.url(slugify(tag.name))
        return photo

    def height(self):
        if not hasattr(self, 'size'):
            self.size = self.get_size()
        return self.size[1]

    def width(self):
        if not hasattr(self, 'size'):
            self.size = self.get_size()
        return self.size[0]

    def get_size(self):
        ex = self.get_exported()
        media_path = settings.GALLERY_SETTINGS.get('media_path')
        full_path = open(os.path.join(media_path, ex.normal_relpath))
        i = Image.open(full_path)
        return i.size

    def get_exif_infos(self):
        media_path = settings.GALLERY_SETTINGS.get('media_path')
        ex = self.get_exported()
        f = open(os.path.join(media_path, ex.normal_relpath))
        data = EXIF.process_file(f)

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
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, blank=True, maxlength=255)
    category_id = models.IntegerField(null=True, blank=True)
    is_category = models.BooleanField(null=True, blank=True)
    sort_priority = models.IntegerField(null=True, blank=True)
    icon = models.TextField(blank=True)
    
    class Meta:
        db_table = 'tags'

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
        tags = [ t for t in list(Tag.objects.all())
                 if slugify(t.name) in tag_names ]
        final_set = []
        for tag in tags:
            final_set.extend(tag.photo_set.all())
        return final_set

    @classmethod
    def with_name(cls, slugified):
        tags = [ t for t in list(Tag.objects.all())
                 if slugify(t.name) == slugified ]
        if tags:
            tag = tags[0]
        else:
            tag = None
        return tag

    @classmethod
    def get_cloud(self, *containing_tags):
        cloud = []
        sql = ('select t.name, count(pt.photo_id)'
               '       from photo_tags pt, tags t'
               '       where t.id=pt.tag_id  and pt.tag_id not in (select category_id from tags)')
        if containing_tags:
            sql += (' and pt.photo_id in'
                    '     (select distinct pt.photo_id from'
                    '      tags t, photo_tags pt'
                    '      where t.id=pt.tag_id and (0')
            for tag in containing_tags:
               sql += ' or t.name=%r'
            sql += '))'
            for tag in containing_tags:
               sql += ' and t.name!=%r'
        sql += ' group by t.name order by t.name'
        
        cursor = Tag.objects.db.connection.cursor()
        cursor.execute(sql, tuple(containing_tags + containing_tags))
        words = cursor.fetchall()
        if not words:
            return cloud
        cloud = self._get_cloud(words)
        return cloud

    @classmethod
    def _get_cloud(self, entries):
        ''' distribution algo n tags to b bucket, where b represents
        font size. '''
        cloud = []

        class _Tag:

            def __init__(self, name, count):
                self.name = name
                self.count = count

            def __cmp__(self, other):
                return cmp(self.count, other.count)

            def __repr__(self):
                return "<tag: %s : %s>" % (self.name, self.count)
        
        tag_list = []
        for name, count in entries:
            tag = _Tag(name, count)
            tag_list.append(tag)
        
        nbr_of_buckets = 2
        base_font_size = 1
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
                        font_size = base_font_size + bucket * 2
                        font_set_flag = True
                        url = '%s/tag/%s' % (G_URL, slugify(tag.name))
                        cloud.append({'size': font_size, 'url': url,
                                      'name': tag.name})
        return cloud

    @classmethod
    def get_recent_tags_cloud(cls):
        t = settings.GALLERY_SETTINGS['recent_photos_time']
        date = int(time.time() - t)
        tags = Tag.objects.filter(photo__time__gt=date).distinct()
        return tags

    def get_sub_tags_cloud(self):
        cloud = []
        sql = ('select t.name, count(pt.photo_id)'
               '       from photo_tags pt, tags t'
               '       where t.id=pt.tag_id and t.category_id=%s' % self.id)

        sql += ' group by t.name order by t.name'

        cursor = Tag.objects.db.connection.cursor()
        cursor.execute(sql)
        words = cursor.fetchall()
        if not words:
            return cloud
        cloud = self._get_cloud(words)
        return cloud

    def get_recent_photos(self):
        t = settings.GALLERY_SETTINGS['recent_photos_time']
        date = int(time.time() - t)
        photos = self.photo_set.filter(time__gt=date).distinct()
        return photos

    def url(self):
        return '%s/tag/%s' % (G_URL, slugify(self.name))

    get_absolute_url = url

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
        return Tag.objects.filter(category_id=self.id)
    

def get_root_categories():
    return Tag.objects.filter(is_category=1, category_id=0)


class TagAddon(models.Model):
    tag_id = models.IntegerField()
    #tag = models.ForeignKey('Tag')
    description = models.CharField(maxlength=350)
    
    class Admin:
        pass

class PhotoAddon(models.Model):
    photo_id = models.IntegerField(null=True, blank=True)
    hits = models.IntegerField(default=0)

class Comment(models.Model):
    photo_id = models.IntegerField(null=True, blank=True)
    comment = models.TextField()
    author = models.CharField(maxlength=60)
    website = models.CharField(maxlength=128, blank=True)
    submit_date = models.DateTimeField(blank=True)
    is_openid = models.BooleanField(default=True)
    
    class Admin:
        list_display = ('submit_date', 'photo',)

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
        return Photo.objects.get(id=self.photo_id)
