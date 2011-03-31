from django.conf.urls.defaults import *

urlpatterns = patterns('accounting.views',
    (r'^$', 'index')
)
