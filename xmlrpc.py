
from gallery.models import Tag

exported_functions = ['get_tags', 'get_photos_for_tag']


def get_tags():
    """
    Returns a list of Tags
    """
    return [ tag.as_dict() for tag in Tag.objects.all()]

def get_photos_for_tag(tag_id):
    tag = Tag.objects.get(id=tag_id)
    photos = [ photo.as_dict() for photo in tag.photo_set.all() ]
    return photos
