# Create your views here.
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django import forms

from django.shortcuts import render_to_response, get_object_or_404
from mysite.gallery.models import OriginalExport, Photo, Tag, Comment
from django.conf import settings
import time

def index(request):
    random = OriginalExport.get_random(6)
    tags = Tag.get_cloud()
    t = settings.GALLERY_SETTINGS['recent_photos_time']
    recent = OriginalExport.get_random(6, since=(time.time() - t))
    recent_tags = Tag.get_recent_tags_cloud()
    return render_to_response('gallery/index.html',
                              {'random': random, 'tags': tags,
                               'recent': recent, 'recent_tags': recent_tags})

def photo(request, photo_id, in_tag_name=None):

    manipulator = Comment.AddManipulator()

    if request.POST:
        # If data was POSTed, we're trying to create a new Place.
        new_data = request.POST.copy()

        # Check for errors.
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            # No errors. This means we can save the data!
            manipulator.do_html2python(new_data)
            new_data['photo_id'] = photo_id
            new_comment = manipulator.save(new_data)
            
            # Redirect to the object's "edit" page. Always use a redirect
            # after POST data, so that reloads don't accidently create
            # duplicate entires, and so users don't see the confusing
            # "Repost POST data?" alert box in their browsers.
            return HttpResponseRedirect("/gallery/photo/%s/" % photo_id)
    else:
        # No POST, so we want a brand new form without any data or errors.
        errors = new_data = {}

    # Create the FormWrapper, template, context, response.
    form = forms.FormWrapper(manipulator, new_data, errors)
    
    p = get_object_or_404(Photo, pk=photo_id)
    exported = get_object_or_404(OriginalExport, id=photo_id)
    if in_tag_name:
        tag = Tag.with_name(in_tag_name)
    else:
        tag = None
    previous = p.get_sibling_photo('previous', tag)
    next = p.get_sibling_photo('next', tag)
    return render_to_response('gallery/detail.html', {'tag': tag,
                                                      'photo': p,
                                                      'previous': previous,
                                                      'next': next,
                                                      'exported': exported,
                                                      'form': form,
                                                      })

def photos_in_tag(request, tag_name, photo_id=None, page=None):
    if not page:
        page = 1
    else:
        page = int(page)
    if photo_id:
        return photo(request, photo_id, tag_name)
    else:
        # display all photos of the tag
        tag = Tag.with_name(tag_name)
        if not tag:
            raise Http404

        step = settings.GALLERY_SETTINGS.get('items_by_page')
        total = tag.photo_set.count()
        photos = tag.photo_set.all()
        if page == 1:
            start = 0
        else:
            start = (page-1)* step 
        nb_pages, rest = divmod(total, step)
        end = (page * step) 
        if rest:
            nb_pages += 1
        photos = tag.photo_set.all()[start:end]
        total_pages = range(nb_pages)
        params = {'tag': tag, 'page': page,
                  'nb_pages': nb_pages, 'total_pages': total_pages,
                  'photos': photos}
        return render_to_response('gallery/tag.html', params)
