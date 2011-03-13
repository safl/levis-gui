from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login

def index(request):
    
    return render_to_response(
        'base.content.html', {
            'msg': 'Well, hello there...',
            'err': None
        }
    )

def login(request):
    pass

def logout(request):
    pass