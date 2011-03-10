from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import Http404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.db import connection

from hact.models import Node

import datetime
import time
import pprint

import markdown

def index(request, name, date=None):
    """List of nodes."""
    
    node = None
    node_list = None
    
    try:
        node = Node.objects.values('name', 'date', 'title', 'rendered', 'is_dir').order_by('-date').filter(
            name=name,
        )[0]
    except:
        pass
    
    if node and node['is_dir'] == 1:
        
        node_list = Node.objects.values('name').filter(
            name__icontains=name,
        ).annotate(date=Max('date')).order_by('name')
    
    return render_to_response(
        'hact/index.html',
        {
            'node':       node,
            'node_list':  node_list
        },
        context_instance=RequestContext(request)
    )

def view(request, name, date=None):
    """View content ..."""

    # 1. Node with 'name' exists                => view the node
    # 2. Node does not exist, no credentials    => 404
    # 3. Node does not exist, valid credentials => Redirect to edit
    
    node = None
    node_list = None
    print name
    try:
        node = Node.objects.values('name', 'date', 'title', 'rendered', 'is_dir').order_by('-date').filter(
            name=name,
        )[0]
        response = render_to_response(
            'hact/index.html',
            {
                'node': node,
            },
            context_instance=RequestContext(request)
        )
    except IndexError:
      
        if not request.user.is_authenticated():     # 2.
            raise Http404
        else:                                       # 3.
            response = HttpResponseRedirect("edit")
    
    if node and node['is_dir'] == 1:
        
        node_list = Node.objects.values('name').filter(
            name__icontains=name,
        ).annotate(date=Max('date')).order_by('name')
        response = render_to_response(
            'hact/index.html',
            {
                'node': node,
                'node_list': node_list
            },
            context_instance=RequestContext(request)
        )
    
    return response

def edit(request, name, date=None):
    """Edit..."""
    
    if not request.user.is_authenticated():
        raise Http404
      
    # 1. Node exists          => Get node-data
    # 2. Node does not exist  => Set default node-data    
    # 3. On POST => overwrite Node-data and store it.
    
    msg = 'You are changing an existing node.'
    
    try:                        # 1.
        n = Node.objects.order_by('-date').filter(
            name=name,
        )[0]
    except:                     # 2.
        n = Node(name=name)
        msg = 'You are creating a new node.'
    
    if request.POST:
        n.name      = request.POST['name']
        n.title     = request.POST['title']
        n.content   = request.POST['content']
        n.rendered  = markdown.markdown(request.POST['content'])
        n.date      = datetime.datetime.fromtimestamp(time.time())
        n.save()
        msg = 'You have just updated a node.'
    
    return render_to_response(
        'hact/edit.html',
        {
            'node': n,
            'info_message': msg
        },
        context_instance = RequestContext(request)
    )