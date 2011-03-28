from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

def index(request):
    c = RequestContext(request, {
        'msg': 'Well, hello there...',
        'err': None
    })
    return render_to_response( 'dashboard/index.html', c )
