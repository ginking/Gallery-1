import settings as gal_settings
from django.conf import settings

settings.GALLERY_SETTINGS = gal_settings.GALLERY_SETTINGS
settings.OTHER_DATABASES['gallery'] = gal_settings.db
