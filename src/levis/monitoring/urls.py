from django.conf.urls.defaults import *

urlpatterns = patterns('monitoring.views',
    (r'^$', 'index')
)