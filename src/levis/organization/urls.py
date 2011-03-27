from django.conf.urls.defaults import *
from organization.models import Organization

info_dict = {
    'queryset': Organization.objects.all(),
    'paginate_by': 30
}

urlpatterns = patterns('',
    (r'^add/?$', 'organization.views.add'),
    (r'^index/?$', 'django.views.generic.list_detail.object_list', info_dict),
    (r'^view/(?P<id>\d+)$', 'organization.views.view'),
    (r'^json/?$', 'organization.views.json'),
    (r'^csv/?$', 'organization.views.csv'),
    (r'^pdf/?$', 'organization.views.pdf'),
    (r'^$', 'django.views.generic.list_detail.object_list', info_dict)
)