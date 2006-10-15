
from gallery.models import Tag
from gallery.models import get_root_categories as get_categories

exported_functions = ['get_tags', 'get_root_categories',
                      'get_sub_tags', 'get_photos_for_tag']


def get_root_categories():
    """
    Returns the list of root categories
    """
    return [ t.as_dict() for t in get_categories() ]

def get_tags():
    """
    Returns a flattened list of all Tags
    """
    return [ tag.as_dict() for tag in Tag.objects.all()]

def get_sub_tags(category_id):
    """
    Returns the list of children tags of the given tag category
    """
    tag = Tag.objects.get(id=category_id)
    return [ t.as_dict() for t in tag.get_tags()]

def get_photos_for_tag(tag_id):
    """
    Returns the list of photos stored under given tag
    """
    tag = Tag.objects.get(id=tag_id)
    photos = [ photo.as_dict() for photo in tag.photo_set.all() ]
    return photos
