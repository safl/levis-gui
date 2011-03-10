from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('hact.views',
  ('^$', 'view', {'name':''}), 
  ('^(?P<name>)index/(?:(?P<date>[0-9/]+)/)?$', 'index'),
  ('(?P<name>[a-zA-Z][a-zA-Z_\-/0-9]*)/index/(?:(?P<date>[0-9/]+)/)?$', 'index'),  
  ('(?P<name>[a-zA-Z][a-zA-Z_\-/0-9]*)/edit/(?:(?P<date>[0-9/]+)/)?$', 'edit'),
  ('(?P<name>)edit/(?:(?P<date>[0-9/]+)/)?$', 'edit'),
  ('(?P<name>[a-zA-Z][a-zA-Z_\-/0-9]*)/(?:(?P<date>[0-9/]+)/)?$', 'view'),
)