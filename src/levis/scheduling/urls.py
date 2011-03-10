from django.conf.urls.defaults import *

urlpatterns = patterns('scheduling.views',
    (r'^$', 'index')
)