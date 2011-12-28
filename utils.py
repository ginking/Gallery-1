from django.conf import settings
from gallery import forms as gallery_forms
from gallery.models import Comment
import re, string
import datetime

def beautyfull_text(text):
    """ return a the text w/ some html cosemtics """
    temp = string.replace(text,'\n','<br />\n')
    temp = string.replace(temp,'  ','&nbsp; ')
    temp = re.sub('href=([_\=a-zA-Z\-0-9/:.&?]+)','href=\"\g<1>"',temp)
    temp = re.sub('src=([_\=a-zA-Z\-0-9/:.&?]+)','src=\"\g<1>"',temp)

    return temp

def get_page(page, total):

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

def process_form(request, aksmet, photo_id=None, video_id=None):
    reset_cache = False
    if request.method == 'POST':
        post = dict(request.POST)

        if hasattr(request, 'openid'):
            post['author'] = request.openid.sreg.get('fullname',
                                                     request.openid)
            post['website'] = request.openid
            is_openid = True
        else:
            post['author'] = post['author'][0]
            post['website'] = post['website'][0]
            is_openid = False

        post['comment'] = post['comment'][0]
        form = gallery_forms.CommentForm(post)
        if form.is_valid():
            # Do form processing
            data = form.cleaned_data
            ak_data = {
                'user_ip': request.META.get('REMOTE_ADDR', '127.0.0.1'),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'referrer': request.META.get('HTTP_REFERER', ''),
                'comment_type': 'comment',
                'comment_author': post['author'],
                'comment_author_url': post['website']}
            data['public'] = not aksmet.comment_check(data, ak_data)
            data['comment'] = beautyfull_text(data['comment'])
            data['submit_date'] = datetime.datetime.today()
            data['is_openid'] = is_openid
            data['photo_id'] = photo_id or 0
            data['video_id'] = video_id or 0
            comment = Comment(**data)
            comment.save()
            form = gallery_forms.CommentForm()
            reset_cache = True
        else:
            form = gallery_forms.CommentForm(request.POST)
    else:
        form = gallery_forms.CommentForm()

    return reset_cache, form
