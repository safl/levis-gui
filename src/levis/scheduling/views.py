import logging
import datetime
import pprint
import math
import copy

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.db.models import Q

from scheduling.models import Event

weekday_string = {
        0: 'Monday',
        1: 'Tuesday',
        2: 'Wednesday',
        3: 'Thursday',
        4: 'Friday',
        5: 'Saturday',
        6: 'Sunday'
    }

def occurence(events, start, end):
    occurence = []
    
    date    = start
    delta   = datetime.timedelta(days=1)
    
    while(date <= end):
        
        weekday     = date.weekday()
        weekstart   = date - datetime.timedelta(days=weekday)
        
        for event in events:
            
            offset  = date - event.date_start
            
            first_week_start = (event.date_start - datetime.timedelta(days=event.date_start.weekday()))
            offset_weeks = int(float((date - first_week_start).days) / 7)
            
            dow = { # TODO: this is bad... find a better way of mapping to weekdays
                0: event.mon,
                1: event.tue,
                2: event.wed,
                3: event.thu,
                4: event.fri,
                5: event.sat,
                6: event.sun
            }
            
            if event.frequency.name == "SINGULAR":
                
                occurence.append(copy.copy(event))
            
            if event.frequency.name == "DAILY" and \
                (offset.days % int(event.interval)) == 0:
                                
                e = copy.copy(event)
                e.date_start    = date
                e.date_end      = date
                occurence.append(e)
                
            elif event.frequency.name == "WEEKLY" and \
                dow[weekday] == 1 and \
                offset_weeks % event.interval == 0:
                                
                e = copy.copy(event)
                e.date_start    = date
                e.date_end      = date
                occurence.append(e)
            
            elif event.frequency.name == "MONTHLY_BY_DOM" and \
                date.day == event.interval:
                
                e = copy.copy(event)
                e.date_start    = date
                e.date_end      = date
                occurence.append(e)
                
            elif event.frequency.name == "MONTHY_BY_DOW" and \
                dow[weekday] == 1:
                # Add criteria for first/second etc.
                
                event.date_start    = date
                event.date_end      = date
                occurence.append(event)
        
        date += delta
    
    return occurence

def day(request, date=None):
    
    if date:
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    else:
        date = datetime.date.today()
    
    start   = date-datetime.timedelta(days=7)
    end     = date
    
    weekday = date.weekday()
    q = [
        Q( date_start__lte = start, date_end__gte = end ) |
        Q( date_start__lte = start, date_end__isnull = True ),
    ]
    
    events = Event.objects.filter( *q )
    
    return render_to_response(
        'scheduling/day.html', {
            'weekday': weekday_string[weekday],
            'date': str(date),
            'next': str(date+datetime.timedelta(days=1)),
            'prev': str(date-datetime.timedelta(days=1)),
            'events': occurence(events, start, end),
            'occurence': None,
            'title': 'Scheduling..',
            'err': None,
            'submenu': ['Day', 'Week', 'Month','My Day View']
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
