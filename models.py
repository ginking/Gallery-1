# Also note: You'll have to insert the output of 'django-admin.py sqlinitialdata [appname]'
# into your database.

from django.db import models, connection, connections
from django.conf import settings
from django.template.defaultfilters import slugify

import time
import os, Image
import EXIF

G_URL=settings.GALLERY_SETTINGS['rel_url']

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

    media_url = '%s/media/' % G_URL
    
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
    def get_random(cls, number, since=None):
        if not since:
            objects = cls.objects.order_by('?')[:number]
        else:
            sql = 'select oe.id from original_exports oe, photos p where oe.id=p.id and p.time > %r order by random() limit %r'
            
            connection = OriginalExport.objects.db.connection
            cursor = connection.cursor()
            cursor.execute(sql % (float(since), int(number),))
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
        return "%s%s" % (self.media_url, self.hq_relpath)
        
    def mq_url(self):
        return "%s%s" % (self.media_url, self.mq_relpath)
        

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
                'exported': self.get_exported().as_dict(),
                'description': self.description,
                'exif': [i for i in self.get_exif_infos() if i != ' | '],
                'tags': [tag.name for tag in self.tags.all()]}

    def get_comments(self):
        comments = Comment.objects.filter(photo_id=self.id)
        if not comments:
            comments = []
        return comments

    def url(self, extra=None):
        if hasattr(self, '_url'):
            return self._url
        url = '%s/photo/%s' % (G_URL, self.id)
        if extra:
            if not extra.startswith('/'):
                extra = '/' + extra
            url += extra
        return url

    get_absolute_url = url

    def in_tag_url(self, tag_name):
        return '%s/photo/%s/%s' % (G_URL, self.id, slugify(tag_name))

    def get_exported(self):
        return OriginalExport.objects.get(id=self.id)

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
                if len(infos) > 1:
                    infos.append(' | ')
                infos.append({'title': v, 'value': str(data[k])})

        return infos
    
class Tag(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField(unique=True, blank=True)
    category_id = models.IntegerField(null=True, blank=True)
    is_category = models.BooleanField(null=True, blank=True)
    sort_priority = models.IntegerField(null=True, blank=True)
    icon = models.TextField(blank=True)
    
    class Meta:
        db_table = 'tags'

    class Admin:
        pass

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
                'photo_count': self.photo_set.count()
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
               '       where t.id=pt.tag_id')
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
        
        connection = Tag.objects.db.connection
        cursor = connection.cursor()
        cursor.execute(sql, tuple(containing_tags + containing_tags))
        words = cursor.fetchall()
        if not words:
            return cloud
##        tags = Tag.objects
##         words = [ (t, t.photo_set.count()) for t in tags.order_by('name')]
        most = max([x[1] for x in words])
        thresh = min(int(most * 0.1), 3)
        for tag, count in words:
            if count < thresh:
                continue
            size = (count - thresh)/(most - thresh) * 2.0 + 0.8
            url = '%s/tag/%s' % (G_URL, slugify(tag))
            cloud.append({'size': size, 'url': url, 'name': tag})
        return cloud


    @classmethod
    def get_recent_tags_cloud(cls):
        t = settings.GALLERY_SETTINGS['recent_photos_time']
        date = int(time.time() - t)
        tags = Tag.objects.filter(photo__time__gt=date).distinct()
        return tags
    
    def url(self):
        return '%s/tag/%s' % (G_URL, slugify(self.name))

    get_absolute_url = url

    def get_description(self):
        try:
            description = TagDescription.objects.get(tag_id=self.id)
        except:
            description = None
        if not description:
            description = ''
        else:
            description = description.description
        return description

class TagDescription(models.Model):
    tag_id = models.IntegerField()
    description = models.CharField(maxlength=350)

    class Admin:
        pass


class Comment(models.Model):
    photo_id = models.IntegerField(null=True, blank=True)
    comment = models.TextField()
    author = models.CharField(maxlength=60)
    website = models.CharField(maxlength=128, blank=True)
    time = models.DateTimeField(null=True, auto_now_add=True)
    
    class Admin:
        pass
    
    def __str__(self):
        return "%s on photo %s: %s" % (self.author, self.photo_id,
                                       self.comment[:50])

    def url(self):
        return '%s/comment/%s' % (G_URL, self.id)

    get_absolute_url = url

    def photo(self):
        return Photo.objects.get(id=self.photo_id)
