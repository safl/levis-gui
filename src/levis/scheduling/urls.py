from django.conf.urls.defaults import *

urlpatterns = patterns('scheduling.views',
    (r'^(?P<date>\d{4}-\d{2}-\d{2})?$', 'day'),
    (r'^day/(?P<date>\d{4}-\d{2}-\d{2})?$', 'day'),
    (r'^day_vertical/(?P<date>\d{4}-\d{2}-\d{2})?$', 'day_vertical'),
    (r'^week/(?P<date>\d{4}-\d{2}-\d{2})?$', 'week'),
    (r'^month/(?P<date>\d{4}-\d{2}-\d{2})?$', 'month'),
    
)