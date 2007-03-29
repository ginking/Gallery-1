

GALLERY_SETTINGS={'items_by_page': 20,
                  'media_path': '/home/phil/scaled',
                  'author': 'Philippe Normand',
                  'copyright': 'Copyright &copy; 2006, 2007',
                  'static_path': '/home/phil/devel/gallery/static',
                  'recent_photos_time': 60*60*24*14,
                  'rel_url': '/gallery'}

db = { 'DATABASE_ENGINE': 'sqlite3',
       'DATABASE_NAME': '/data/scaled/db/photos.db',

       # Don't change this, please.
       'MODELS': ['gallery.%s' % m for m in ('Tag', 'Photo',
                                             'OriginalExport')]
       }


