from django.conf.urls.defaults import *
from organization.models import Organization

info_dict = {
    'queryset': Organization.objects.all(),
    'paginate_by': 3
}

urlpatterns = patterns('',
    (r'^$', 'django.views.generic.list_detail.object_list', info_dict)
)