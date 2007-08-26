from django.conf import settings
import re, string

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
