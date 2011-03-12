import datetime

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.db.models import Q

from scheduling.models import Event

def day(request, date=None):
    
    if date:
        today = datetime.datetime.strptime(date, '%Y-%m-%d')
    else:
        today = datetime.date.today()
    
    weekday = today.weekday()
    
    events = Event.objects.filter(
        
        Q( date_start__lte = today, date_end__gte = today ) |
        Q( date_start__lte = today, date_end__isnull = True ),        
        
        #mon = int(weekday==0),
        #tue = int(weekday==1),
        #wed = int(weekday==2),
        #thu = int(weekday==3),
        #fri = int(weekday==4),
        #sat = int(weekday==5),
        #sun = int(weekday==6)
        
    )
    return render_to_response(
        'scheduling/day.html', {
            'events': events,
            'title': 'Well, hello there... %s %d' % (today, weekday),
            'err': None
        }
    )
    
def day_vertical(request):
    return render_to_response(
        'scheduling/day_vertical.html', {
            'events': Event.objects.all(),
            'msg': 'Well, hello there...',
            'err': None
        }
    )

def week(request):
    return render_to_response(
        'scheduling/week.html', {
            'events': Event.objects.all(),
            'msg': 'Well, hello there...',
            'err': None
        }
    )
    
def month(request):
    return render_to_response(
        'scheduling/month.html', {
            'events': Event.objects.all(),
            'msg': 'Well, hello there...',
            'err': None
        }
    )
