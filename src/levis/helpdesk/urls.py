from django.conf.urls.defaults import *
from helpdesk.models import Ticket

info_dict = {
    'queryset': Ticket.objects.all(),
    'paginate_by': 10
}

urlpatterns = patterns('',
    (r'^$', 'django.views.generic.list_detail.object_list', info_dict)
)