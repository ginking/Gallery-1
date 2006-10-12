

GALLERY_SETTINGS={'items_by_page': 20,
                  'media_path': '/home/phil/scaled',
                  'static_path': '/home/phil/inc',
                  'recent_photos_time': 60*60*24*14,
                  'rel_url': '/gallery'}

db = { 'DATABASE_ENGINE': 'sqlite3',
       'DATABASE_NAME': '/home/phil/scaled/db/photos.db',
       'MODELS': ['gallery.%s' % m for m in ('Tag', 'Photo',
                                             'OriginalExport')]
       }


