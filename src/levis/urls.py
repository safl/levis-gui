from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^static/(?P<path>.*)$',
        'django.views.static.serve',
        {'document_root': '/home/safl/Desktop/levis/src/static'}
    ),
    
    (r'', include('dashboard.urls')),
    (r'^accounting/', include('accounting.urls')),
    (r'^dashboard/', include('dashboard.urls')),
    (r'^helpdesk/', include('helpdesk.urls')),
    (r'^monitoring/', include('monitoring.urls')),
    (r'^organization/', include('organization.urls')),
    (r'^scheduling/', include('scheduling.urls')),
    (r'^reports/', include('reports.urls')),
    (r'^knowledge/', include('hact.urls')),

    (r'^admin/', include(admin.site.urls)),
)
