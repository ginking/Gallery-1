from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, \
     get_list_or_404
from gallery.models import OriginalExport, Photo, Tag, Event, \
     OriginalVideoExport, Video
from gallery.utils import process_form, get_page
from django.template import RequestContext
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.core.paginator import Paginator, InvalidPage, EmptyPage

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
if not aksmet.key:
    # apikey.txt not found, use settings.
    aksmet.setAPIKey(settings.GALLERY_SETTINGS['akismet_api_key'],
                     settings.GALLERY_SETTINGS['blog_url'])

def index(request):
    random = Photo.get_random(8)
    tags = Tag.get_cloud()
    t = settings.GALLERY_SETTINGS['recent_photos_time']
    recent = Photo.get_random(8, since=(time.time() - t))
    recent_tags = Tag.get_recent_tags_cloud()
    params = {'random': random, 'tags': tags,
              'recent': recent, 'recent_tags': recent_tags}
    if hasattr(request, 'openid'):
        params['openid'] = request.openid
    params.update(DEFAULT_PARAMS)
    return render_to_response('gallery/index.html', params,
                              context_instance=RequestContext(request))
index = cache_page(index, CACHE_TIMEOUT)

def recent(request, tag_name=None, page=None):
    tag = Tag.with_name(tag_name)
    if not tag:
        photo_set = Photo.recent()
        video_set = Video.recent()
    else:
        photo_set = tag.get_recent_photos()
        video_set = tag.get_recent_videos()

    media_set = list(photo_set) + list(video_set)
    total = len(media_set)
    page, start, end, nb_pages = get_page(page, total)

    medias = media_set[start:end]
    total_pages = range(nb_pages)

    slug = '/%s/recent/' % G_URL
    if tag_name:
        slug += '%s/' % tag_name

    params = {'tag': tag, 'page': page, 'slug': slug, 'tag_name': tag_name,
              'nb_pages': nb_pages, 'total_pages': total_pages,
              'medias': medias}
    params.update(DEFAULT_PARAMS)
    return render_to_response('gallery/tag.html', params,
                              context_instance=RequestContext(request))
recent = cache_page(recent, CACHE_TIMEOUT)

def date(request, year, month, day, page=None):
    year = int(year)
    month = int(month)
    day = int(day)
    photo_set = Photo.for_date(year, month, day)
    video_set = Video.for_date(year, month, day)
    media_set = list(photo_set) + list(video_set)

    total = len(media_set)
    page, start, end, nb_pages = get_page(page, total)

    medias = media_set[start:end]
    total_pages = range(nb_pages)
    slug = '%s/date/%s/%s/%s/' % (G_URL, year, month, day)

    human_date = datetime.date(year, month, day).strftime('%A %d %B')
    
    params = {'year': year, 'month': month, 'day': day,
              'page': page, 'slug': slug,
              'human_date': human_date,
              'nb_pages': nb_pages, 'total_pages': total_pages,
              'medias': medias}
    params.update(DEFAULT_PARAMS)
    return render_to_response('gallery/date.html', params,
                              context_instance=RequestContext(request))
date = cache_page(date, CACHE_TIMEOUT)

def photo(request, photo_id, in_tag_name=None, in_event_id=None):
    reset_cache, form = process_form(request, aksmet, photo_id=photo_id)

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

        tag = None
        event = None
        if in_tag_name:
            tag = Tag.with_name(in_tag_name)
            kw = dict(tag=tag)
        elif in_event_id:
            kw = dict(event_id=in_event_id)
            event = get_object_or_404(Event.objects.using("gallery"), pk=in_event_id)
        else:
            kw = {}
        previous = p.get_sibling_media('previous', **kw)
        next = p.get_sibling_media('next', **kw)
        p.increment_hit()
        slug = '/%s/photo/%s/' % (G_URL, p.id)
        params = {'tag': tag, 'media': p, 'previous': previous,
                  'slug': slug, 'next': next, 'exported': exported,
                  'form': form, 'event': event}
        params.update(DEFAULT_PARAMS)
        context = RequestContext(request)
        response = render_to_response('gallery/photo.html', params,
                                      context_instance=context)
        cache.set(cache_key, response, CACHE_TIMEOUT)
    return response

def video(request, video_id, in_tag_name=None, in_event_id=None):
    reset_cache, form = process_form(request, aksmet, video_id=video_id)

    response = None
    cache_key = 'video_%s' % video_id

    if not reset_cache:
        response = cache.get(cache_key)
        if not response:
            reset_cache = True

    if reset_cache or not response:
        v = get_object_or_404(Video.objects.using("gallery"), pk=video_id)
        exported = get_object_or_404(OriginalVideoExport.objects.using("gallery"),
                                     id=video_id)

        tag = None
        event = None
        if in_tag_name:
            tag = Tag.with_name(in_tag_name)
            kw = dict(tag=tag)
        elif in_event_id:
            kw = dict(event_id=in_event_id)
            event = get_object_or_404(Event.objects.using("gallery"), pk=in_event_id)
        else:
            kw = {}
        previous = v.get_sibling_media('previous', **kw)
        next = v.get_sibling_media('next', **kw)
        v.increment_hit()
        slug = '/%s/video/%s/' % (G_URL, v.id)
        params = {'tag': tag, 'media': v, 'previous': previous,
                  'slug': slug, 'next': next, 'exported': exported,
                  'form': form, 'event': event}
        params.update(DEFAULT_PARAMS)
        context = RequestContext(request)
        response = render_to_response('gallery/video.html', params,
                                      context_instance=context)
        cache.set(cache_key, response, CACHE_TIMEOUT)
    return response

def medias_in_tag(request, tag_name, photo_id=None, video_id=None, page=None):
    if photo_id:
        return photo(request, photo_id, in_tag_name=tag_name)
    elif video_id:
        return video(request, video_id, in_tag_name=tag_name)
    else:
        if tag_name.find('+') > -1:
            # combination of tags
            media_set = Tag.build_set(tag_name)
            tag = None
        else:
            # display all photos of the tag
            tag = Tag.with_name(tag_name)
            if not tag:
                raise Http404
            else:
                photo_set = tag.photo_set.order_by('timestamp')
                video_set = tag.video_set.order_by('time_created')
                media_set = list(photo_set) + list(video_set)

        total = len(media_set)
        page, start, end, nb_pages = get_page(page, total)

        medias = media_set[start:end]
        total_pages = range(nb_pages)
        slug = '%s/tag/%s/' % (G_URL, tag_name)
        params = {'tag': tag, 'page': page, 'slug': slug, 'tag_name': tag_name,
                  'nb_pages': nb_pages, 'total_pages': total_pages,
                  'medias': medias}
        params.update(DEFAULT_PARAMS)
        return render_to_response('gallery/tag.html', params,
                                  context_instance=RequestContext(request))
medias_in_tag = cache_page(medias_in_tag, CACHE_TIMEOUT)

def medias_in_event(request, media_type=None, media_id=None, event_id=None):
    if media_type == "photo":
        return photo(request, media_id, in_event_id=event_id)
    else:
        return video(request, media_id, in_event_id=event_id)
medias_in_event = cache_page(medias_in_event, CACHE_TIMEOUT)

def events(request):
    slug = ''
    Events = Event.objects.using("gallery")

    qset = Events

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 0
    before = request.GET.get('before')
    after = request.GET.get('after')

    if before:
        qset = Events.filter(time_created__lt=before)
        slug = "&before=%s" % before
    elif after:
        qset = Events.filter(time_created__gt=after)
        slug += "&after=%s" % after
    elif not page:
        page = 1

    if page:
        events = get_list_or_404(qset.order_by('-time_created'))
        paginator = Paginator(events, 10) # Show 10 events per page

        # If page request (9999) is out of range, deliver last page of results.
        try:
            events = paginator.page(page)
        except (EmptyPage, InvalidPage):
            events = paginator.page(paginator.num_pages)
    else:
        events = get_list_or_404(qset.order_by('-time_created')[:10])

    params = {'events': events, 'slug_foot': slug}
    params.update(DEFAULT_PARAMS)
    return render_to_response('gallery/events.html', params)
events = cache_page(events, CACHE_TIMEOUT)

def event(request, event_id):
    event = get_object_or_404(Event.objects.using("gallery"), pk=event_id)
    slug = '%s/events' % G_URL
    params = {'event': event, 'slug': slug}
    params.update(DEFAULT_PARAMS)
    return render_to_response('gallery/event.html', params)
event = cache_page(event, CACHE_TIMEOUT)

