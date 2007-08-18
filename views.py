from django.http import Http404, HttpResponse, HttpResponseRedirect
#from django import forms
from django import newforms as forms
from django.shortcuts import render_to_response, get_object_or_404
from gallery.models import OriginalExport, Photo, Tag, Comment
from gallery import forms as gallery_forms
from django.template import RequestContext
from django.conf import settings
import datetime, time

DEFAULT_PARAMS={'author': settings.GALLERY_SETTINGS['author'],
                'copyright': settings.GALLERY_SETTINGS['copyright']
                }

def index(request):
    random = OriginalExport.get_random(8)
    tags = Tag.get_cloud()
    t = settings.GALLERY_SETTINGS['recent_photos_time']
    recent = OriginalExport.get_random(8, since=(time.time() - t))
    recent_tags = Tag.get_recent_tags_cloud()
    params = {'random': random, 'tags': tags,
              'recent': recent, 'recent_tags': recent_tags,
              'openid': request.openid}
    params.update(DEFAULT_PARAMS)
    return render_to_response('gallery/index.html', params,
                              context_instance=RequestContext(request))

def popular(request, tag_name=None):
    photos = Photo.popular(tag_name)
    params = {'photos': photos}
    return render_to_response('gallery/popular.html', params,
                              context_instance=RequestContext(request))
    

def date(request, year, month, day, page=None):
    year = int(year)
    month = int(month)
    day = int(day)
    photo_set = Photo.for_date(year, month, day)

    total = len(photo_set)
    page, start, end, nb_pages = _get_page(page, total)

    photos = photo_set[start:end]
    total_pages = range(nb_pages)
    slug = '/gallery/date/%s/%s/%s/' % (year, month, day)

    human_date = datetime.date(year, month, day).strftime('%A %d %B')
    
    params = {'year': year, 'month': month, 'day': day,
              'page': page, 'slug': slug,
              'human_date': human_date,
              'nb_pages': nb_pages, 'total_pages': total_pages,
              'photos': photos}
    params.update(DEFAULT_PARAMS)
    return render_to_response('gallery/date.html', params,
                              context_instance=RequestContext(request))

    

def photo(request, photo_id, in_tag_name=None):
    
    CommentForm = gallery_forms.CommentForm
    if request.method == 'POST':
        post = dict(request.POST)
        
        if request.openid:
            post['author'] = request.openid.sreg.get('fullname',
                                                     request.openid)
            post['website'] = request.openid
            is_openid = True
        else:
            post['author'] = post['author'][0]
            post['website'] = post['website'][0]
            is_openid = False
            
        post['comment'] = post['comment'][0]
        form = CommentForm(post)
        if form.is_valid():
            # Do form processing
            data = form.clean_data
            data['photo_id'] = photo_id
            data['submit_date'] = datetime.datetime.today()
            data['is_openid'] = is_openid
            comment = Comment(**data)
            comment.save()
            form = CommentForm()
        else:
            print form.errors, form['website']
            form = CommentForm(request.POST)
    else:
        form = CommentForm()
    p = get_object_or_404(Photo, pk=photo_id)
    exported = get_object_or_404(OriginalExport, id=photo_id)
    if in_tag_name:
        tag = Tag.with_name(in_tag_name)
    else:
        tag = None
    previous = p.get_sibling_photo('previous', tag)
    next = p.get_sibling_photo('next', tag)
    p.increment_hit()
    slug = '/gallery/photo/%s/' % p.id
    params = {'tag': tag, 'photo': p, 'previous': previous, 'slug': slug,
              'next': next, 'exported': exported, 'form': form}
    params.update(DEFAULT_PARAMS)
    return render_to_response('gallery/detail.html', params,
                              context_instance=RequestContext(request))

def photos_in_tag(request, tag_name, photo_id=None, page=None):
    if photo_id:
        return photo(request, photo_id, tag_name)
    else:
        if tag_name.find('+') > -1:
            # combination of tags
            photo_set = Tag.build_set(tag_name)
            tag = None
        else:
            # display all photos of the tag
            tag = Tag.with_name(tag_name)
            if not tag:
                raise Http404
            else:
                photo_set = tag.photo_set.all()

        if len(photo_set) == 0:
            return category(request, tag)

        total = len(photo_set)
        page, start, end, nb_pages = _get_page(page, total)
            
        photos = photo_set[start:end]
        total_pages = range(nb_pages)
        slug = '/gallery/tag/%s/' % tag_name
        params = {'tag': tag, 'page': page, 'slug': slug, 'tag_name': tag_name,
                  'nb_pages': nb_pages, 'total_pages': total_pages,
                  'photos': photos}
        params.update(DEFAULT_PARAMS)
        return render_to_response('gallery/tag.html', params,
                                  context_instance=RequestContext(request))

def category(request, tag):

    params = {'tags': tag.get_sub_tags_cloud(),
              'tag': tag,
              'random': OriginalExport.get_random(10, category_id=tag.id)
              }
    params.update(DEFAULT_PARAMS)    
    return render_to_response('gallery/category.html', params,
                              context_instance=RequestContext(request))

def _get_page(page, total):

    if not page:
        page = 1
    else:
        page = int(page)

    step = settings.GALLERY_SETTINGS.get('items_by_page')
    if page == 1:
        start = 0
    else:
        start = (page-1)* step

    nb_pages, rest = divmod(total, step)
    end = (page * step) 
    if rest:
        nb_pages += 1

    return page, start, end, nb_pages
