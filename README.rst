
How to install this ?
=====================

1. Install Django :)
2. Start a new project and configure it:

   ::

     $ django-admin.py startproject mysite
     $ cd mysite
     $ # edit settings.py and configure the DATABASE. advice: use a
         sqlite db :)
     $ python manage.py syncdb

3. Activate the admin interface, see
   http://www.djangoproject.com/documentation/tutorial2/ and configure
   your site'url


4. Now you have a Django site, you can install the Gallery application

   ::

     $ cd ..
     $ mv gallery mysite/
     $ cd mysite
     $ # add 'mysite.gallery' to setting.py INSTALLED_APPS
     $ # configure the gallery by editing gallery/settings.py,
     $ # register the 'gallery' db in DATABASES

   ::

     $ python manage.py sql gallery

   This outputs a bunch of SQL commands, you'll need to execute them
   in your site's sqlite db, but only the ones for <default>
   connection:

   ::

     $ sqlite3 site.db
     sqlite> # create table gallery_tagaddon gallery_photoaddon and
               gallery_comment

5. Now you need to bind the gallery's urls to your django site:

   ::
   
     $ # edit site/urls.py and add this:

         (r'^gallery/', include('mysite.gallery.urls')),

       # in urlpatterns variable

   This will bind all urls starting with gallery/ to the gallery
   application.


6. Start the testing server

   ::

     $ python manage.py runserver


7. Enjoy :)
