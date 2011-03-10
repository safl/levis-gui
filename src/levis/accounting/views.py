from django.http import HttpResponse
from django.shortcuts import render_to_response

def index(request):
    return render_to_response(
        'dashboard/index.html', {
            'msg': 'Well, hello there...',
            'err': None
        }
    )
