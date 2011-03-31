import json as jsonlib
import csv as csvlib

from reportlab.pdfgen import canvas

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.contrib.auth import authenticate, login
from django.template import RequestContext

from organization.models import Organization, OrganizationForm

def add(request):
        
    if request.method == 'POST':
        form = OrganizationForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('index')
    else:
        form = OrganizationForm()

    c = RequestContext(request, {
        'form': form,
        'appname': 'organization',
        'submenu': [('index', 'Browse'), ('add', 'Add')]
    })
    c.update(csrf(request))
    
    return render_to_response('base.fieldset.form.html', c)

def view(request, id):
    
    o = Organization.objects.get(pk=id)
    
    c = RequestContext(request, {
        'organization': o
    })
    
    return render_to_response('organization/view.html', c)

def login(request):
    pass

def logout(request):
    pass

# Alternate data representation
def json(request):
    response = HttpResponse(mimetype='text/json')
    response['Content-Disposition'] = 'attachment; filename=organizations.json'

    s = jsonlib.dumps(
        [o.__map__() for o in Organization.objects.all()]
    )
    response.write(s)
    return response

def csv(request):
    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=organizations.csv'
    
    writer = csvlib.writer(response)
    for o in Organization.objects.all():
        writer.writerow(o.__list__())

    return response

def pdf(request):
    
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=somefilename.pdf'

    p = canvas.Canvas(response)
    
    for c, o in enumerate(Organization.objects.all()):
        p.drawString(0, 10*c, str(o))
    
    p.showPage()
    p.save()
    
    return response