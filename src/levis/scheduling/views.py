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

def occurence(start, end):
    
    q = [
        Q( date_start__lte = start, date_end__gte = end ) |
        Q( date_start__lte = start, date_end__isnull = True ),
    ]
    
    events = Event.objects.filter( *q )
    
    occurence = []
    
    date    = start
    delta   = datetime.timedelta(days=1)
    
    while(date <= end):
        
        weekday     = date.weekday()
        weekstart   = date - datetime.timedelta(days=weekday)
        
        for event in events:
            
            offset          = date - event.date_start            
            offset_weeks    = int(float((date - (event.date_start - datetime.timedelta(days=event.date_start.weekday()))).days) / 7)
            
            som = datetime.date(    # Start of the month
                date.year,
                date.month,
                1
            )
            
            dow = { # TODO: this is bad... find a better way of mapping to weekdays
                0: event.mon,
                1: event.tue,
                2: event.wed,
                3: event.thu,
                4: event.fri,
                5: event.sat,
                6: event.sun
            }
            event.top = event.time_start.hour * 42
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
    
    today = datetime.date.today()
    if date:
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    else:
        date = today
    
    start   = date
    end     = date
    prev    = date-datetime.timedelta(days=1)
    next    = date+datetime.timedelta(days=1)
    
    weekday = date.weekday()    
        
    return render_to_response(
        'scheduling/day.html', {
            'weekday': weekday_string[weekday],
            'weeknumber': date.isocalendar()[1],
            'today': str(today),
            'date': date,
            'next': str(next),
            'prev': str(prev),
            'events': occurence(start, end),
            'slots': xrange(0, 24),
            'title': 'Scheduling..',
            'err': None,
            'submenu': ['Day', 'Week', 'Month', 'Day Vertical', 'Week Vertical', 'Agenda']
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
