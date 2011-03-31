from django.conf.urls.defaults import *

urlpatterns = patterns('scheduling.views',
    (r'^(?P<date>\d{4}-\d{2}-\d{2})?$', 'day'),
    (r'^day/(?P<date>\d{4}-\d{2}-\d{2})?$', 'day'),    
    (r'^week/(?P<date>\d{4}-\d{2}-\d{2})?$', 'week'),
    (r'^month/(?P<date>\d{4}-\d{2}-\d{2})?$', 'month'),
    
    (r'^my_day/(?P<date>\d{4}-\d{2}-\d{2})?$', 'my_day'),
    (r'^my_week/(?P<date>\d{4}-\d{2}-\d{2})?$', 'my_week'),
    (r'^my_month/(?P<date>\d{4}-\d{2}-\d{2})?$', 'my_month'),
    (r'^my_agenda/(?P<date>\d{4}-\d{2}-\d{2})?$', 'my_agenda'),    
    
)