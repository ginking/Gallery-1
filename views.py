from django.http import Http404, HttpResponse, HttpResponseRedirect
from django import forms
from django.shortcuts import render_to_response, get_object_or_404, \
     get_list_or_404
from gallery.models import OriginalExport, Photo, Tag, Comment, Roll
from gallery import forms as gallery_forms
from gallery.utils import beautyfull_text, get_page
from django.template import RequestContext
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.core.cache import cache

import datetime, time
import akismet

DEFAULT_PARAMS={'author': settings.GALLERY_SETTINGS['author'],
                'copyright': settings.GALLERY_SETTINGS['copyright'],
                'rel_url': settings.GALLERY_SETTINGS['rel_url']
                }
G_URL=settings.GALLERY_SETTINGS['rel_url']

# 10 minuts
CACHE_TIMEOUT=60*10

aksmet = akismet.Akismet()
aksmet.setAPIKey(settings.GALLERY_SETTINGS['akismet_api_key'],
                 settings.GALLERY_SETTINGS['blog_url'])

def index(request):
    random = OriginalExport.get_random(8)
    tags = Tag.get_cloud()
    t = settings.GALLERY_SETTINGS['recent_photos_time']
    recent = OriginalExport.get_random(8, since=(time.time() - t))
    recent_tags = Tag.get_recent_tags_cloud()
    params = {'random': random, 'tags': tags,
              'recent': recent, 'recent_tags': recent_tags}
    if hasattr(request, 'openid'):
        params['openid'] = request.openid
    params.update(DEFAULT_PARAMS)
    return render_to_response('gallery/index.html', params,
                              context_instance=RequestContext(request))
index = cache_page(index, CACHE_TIMEOUT)

def popular(request, tag_name=None):
    photos = Photo.popular(tag_name)
    params = {'photos': photos}
    return render_to_response('gallery/popular.html', params,
                              context_instance=RequestContext(request))
popular = cache_page(popular, CACHE_TIMEOUT)

def recent(request, tag_name=None, page=None):
    tag = Tag.with_name(tag_name)
    if not tag:
        photo_set = Photo.recent()
    else:
        photo_set = tag.get_recent_photos()

    total = len(photo_set)
    page, start, end, nb_pages = get_page(page, total)

    photos = photo_set[start:end]
    total_pages = range(nb_pages)

    slug = '/%s/recent/' % G_URL
    if tag_name:
        slug += '%s/' % tag_name

    params = {'tag': tag, 'page': page, 'slug': slug, 'tag_name': tag_name,
              'nb_pages': nb_pages, 'total_pages': total_pages,
              'photos': photos}
    params.update(DEFAULT_PARAMS)
    return render_to_response('gallery/tag.html', params,
                              context_instance=RequestContext(request))
recent = cache_page(recent, CACHE_TIMEOUT)

def date(request, year, month, day, page=None):
    year = int(year)
    month = int(month)
    day = int(day)
    photo_set = Photo.for_date(year, month, day)

    total = len(photo_set)
    page, start, end, nb_pages = get_page(page, total)

    photos = photo_set[start:end]
    total_pages = range(nb_pages)
    slug = '%s/date/%s/%s/%s/' % (G_URL, year, month, day)

    human_date = datetime.date(year, month, day).strftime('%A %d %B')
    
    params = {'year': year, 'month': month, 'day': day,
              'page': page, 'slug': slug,
              'human_date': human_date,
              'nb_pages': nb_pages, 'total_pages': total_pages,
              'photos': photos}
    params.update(DEFAULT_PARAMS)
    return render_to_response('gallery/date.html', params,
                              context_instance=RequestContext(request))
date = cache_page(date, CACHE_TIMEOUT)

def photo(request, photo_id, in_tag_name=None):

    reset_cache = False
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
            ak_data = { 
                'user_ip': request.META.get('REMOTE_ADDR', '127.0.0.1'), 
                'user_agent': request.META.get('HTTP_USER_AGENT', ''), 
                'referrer': request.META.get('HTTP_REFERER', ''), 
                'comment_type': 'comment', 
                'comment_author': post['author'],
                'comment_author_url': post['website']}
            data['public'] = not aksmet.comment_check(data, ak_data)
            
            data['comment'] = beautyfull_text(data['comment'])
            data['photo_id'] = photo_id
            data['submit_date'] = datetime.datetime.today()
            data['is_openid'] = is_openid
            comment = Comment(**data)
            comment.save()
            form = CommentForm()
            reset_cache = True
        else:
            form = CommentForm(request.POST)
    else:
        form = CommentForm()

    response = None
    cache_key = 'photo_%s' % photo_id
    
    if not reset_cache:
        response = cache.get(cache_key)
        if not response:
            reset_cache = True

    if reset_cache or not response:
        p = get_object_or_404(Photo.objects.using("gallery"), pk=photo_id)
        exported = get_object_or_404(OriginalExport.objects.using("gallery"),
                                     id=photo_id)

        if in_tag_name:
            tag = Tag.with_name(in_tag_name)
        else:
            tag = None
        previous = p.get_sibling_photo('previous', tag)
        next = p.get_sibling_photo('next', tag)
        p.increment_hit()
        slug = '/%s/photo/%s/' % (G_URL, p.id)
        params = {'tag': tag, 'photo': p, 'previous': previous,
                  'slug': slug, 'next': next, 'exported': exported,
                  'form': form}
        params.update(DEFAULT_PARAMS)
        context = RequestContext(request)
        response = render_to_response('gallery/detail.html', params,
                                      context_instance=context)
        cache.set(cache_key, response, CACHE_TIMEOUT)
    return response

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
        page, start, end, nb_pages = get_page(page, total)
            
        photos = photo_set[start:end]
        total_pages = range(nb_pages)
        slug = '/%s/tag/%s/' % (G_URL, tag_name)
        params = {'tag': tag, 'page': page, 'slug': slug, 'tag_name': tag_name,
                  'nb_pages': nb_pages, 'total_pages': total_pages,
                  'photos': photos}
        params.update(DEFAULT_PARAMS)
        return render_to_response('gallery/tag.html', params,
                                  context_instance=RequestContext(request))
photos_in_tag = cache_page(photos_in_tag, CACHE_TIMEOUT)

def category(request, tag):

    params = {'tags': tag.get_sub_tags_cloud(),
              'tag': tag,
              'random': OriginalExport.get_random(10, category_id=tag.id)
              }
    params.update(DEFAULT_PARAMS)    
    return render_to_response('gallery/category.html', params,
                              context_instance=RequestContext(request))
category = cache_page(category, CACHE_TIMEOUT)

def rolls(request):
    # 10 most recent rolls
    rolls = get_list_or_404(Roll.objects.using("gallery").order_by('-time')[:10])
    return render_to_response('gallery/rolls.html', {'rolls': rolls},
                              context_instance=RequestContext(request))
rolls = cache_page(rolls, CACHE_TIMEOUT)

def roll(request, roll_id):
    roll = get_object_or_404(Roll.objects.using("gallery"), pk=roll_id)
    slug = '/%s/rolls' % G_URL
    return render_to_response('gallery/roll.html', {'roll': roll, 'slug': slug},
                              context_instance=RequestContext(request))
roll = cache_page(roll, CACHE_TIMEOUT)
