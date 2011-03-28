#!/usr/bin/env python
from django.conf import settings

def filter(request):
    context_extras = {}
    return context_extras

def menu(request):
    
    parts  = request.META["PATH_INFO"][1:].split('/', 3)
    cur_appname = 'Unknown'
    cur_action  = 'Unknown'
    
    if len(parts) == 2:
        (cur_appname, cur_view) = parts
    elif len(parts) == 3:
        (cur_appname, cur_view, _) = parts
    
    menu    = []
    submenu = []
    for appname, sub in settings.MENU_TREE:
        menu.append((appname, appname.capitalize()))
        if appname == cur_appname and sub:
            submenu = sub
            
    context_extras = {
        'menu':     menu,
        'submenu':  submenu,
        'appname':  cur_appname,
        'view':   cur_view
    }
    return context_extras