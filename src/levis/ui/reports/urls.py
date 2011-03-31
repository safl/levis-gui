from django.conf.urls.defaults import *

urlpatterns = patterns('reports.views',
    (r'^$', 'index')
)
