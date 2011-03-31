from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext

def index(request):
    
    c = RequestContext(request, {
        'appname': 'reports',
        'action':   'index',
        'submenu':  [('index', 'Browse'), ('adhoc', 'Adhoc'), ('-',''), ('define', 'Define'), ('template', 'Templates')]
    })    
    
    return render_to_response(
        'base.fieldset.html', {
            'msg': 'Well, hello there...',
            'err': None
        },
        context_instance=c
    )
