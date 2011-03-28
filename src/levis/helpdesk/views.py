from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

def index(request):
    
    c = RequestContext(request, {
        'submenu': ['Browse', 'New Ticket'],
        'err': None
    })
    
    return render_to_response( 'base.content.html', c )
