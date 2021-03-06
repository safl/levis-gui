import logging
import datetime
import calendar
import pprint
import math
import copy

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.db.models import Q
from django.template import RequestContext

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
    
    occurences = []
    
    date    = start
    delta   = datetime.timedelta(days=1)
    
    earliest = 1008
    while(date <= end):
        
        occurence = []
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
            event.left = event.time_start.hour * 84
            d_end = datetime.timedelta(
                hours   = event.time_end.hour,
                minutes = event.time_end.minute
            )
            d_start = datetime.timedelta(
                hours   = event.time_start.hour,
                minutes = event.time_start.minute
            )
            d_elapsed = d_end - d_start
            event.elapsed = ((d_elapsed.seconds /60)/60)*42
            
            do_append = False
            if event.frequency.name == "SINGULAR":
                
                do_append = True
            
            if event.frequency.name == "DAILY" and \
                (offset.days % int(event.interval)) == 0:
                
                do_append = True                
                
            elif event.frequency.name == "WEEKLY" and \
                dow[weekday] == 1 and \
                offset_weeks % event.interval == 0:
                
                do_append = True                
            
            elif event.frequency.name == "MONTHLY_BY_DOM" and \
                date.day == event.interval:
                
                do_append = True
                
            elif event.frequency.name == "MONTHY_BY_DOW" and \
                dow[weekday] == 1:
                # Add criteria for first/second etc.
                
                do_append = True
                
            if do_append:
                e = copy.copy(event)
                e.date_start    = date
                e.date_end      = date
                occurence.append(e)
                
                hmm = (d_start.seconds / 60 / 60) * 42
                if hmm < earliest:
                    earliest = hmm
                
        occurences.append(occurence)
        date += delta
    
    return (occurences, earliest)

def view(request, view, start, end, prev, next, weekday):
    
    today = datetime.date.today()
    date    = start
    
    day     = start
    days    = []
    while(day<=end):
        days.append(day)
        day+= datetime.timedelta(days=1)
    (events, earliest) = occurence(start, end)
    
    c = RequestContext(request, {
        'date': date,
        'days': days,
        'today': today,
        'start': start,
        'end': end,
        'next': next,
        'prev': prev,
        'earliest': earliest,
        'kinck': len(events) *42,
        'events': events,
        'slots': ["%02d:00" % slot for slot in xrange(0, 24)],
        'title': 'Scheduling..'
    })
    
    return render_to_response( 'scheduling/%s.html' % view, c )

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
        
    return view(request, 'horizontal', start, end, prev, next, weekday)
    
def week(request, date=None):
    
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
    
    return view(request, 'week', start, end, prev, next, weekday)

def month(request, date=None):
    
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
        
    return view(request, 'month', start, end, prev, next, weekday)

def my_day(request, date=None):
    
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
        
    return view(request, 'vertical', start, end, prev, next, weekday)

def my_week(request, date=None):
    
    today = datetime.date.today()
    if date:
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    else:
        date = today
    
    date = date-datetime.timedelta(days=date.weekday())
    
    start   = date
    end     = date+datetime.timedelta(days=6)    
    
    prev    = date-datetime.timedelta(days=6)
    next    = date+datetime.timedelta(days=7)
    
    weekday = date.weekday()
        
    return view(request, 'vertical', start, end, prev, next, weekday)
    
def my_month(request, date=None):
    
    today = datetime.date.today()
    if date:
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    else:
        date = today
    
    (month_weekday, end_day) = calendar.monthrange(date.year, date.month)
    date    = datetime.date(date.year, date.month, 1)
    
    start   = datetime.date(date.year, date.month, 1)
    end     = datetime.date(date.year, date.month, end_day)
    
    prev    = start-datetime.timedelta(days=1)
    next    = end+datetime.timedelta(days=1)
    
    weekday = date.weekday()
        
    return view(request, 'vertical', start, end, prev, next, weekday)

def my_agenda(request, date=None):
    
    today = datetime.date.today()
    if date:
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    else:
        date = today
    
    start   = date
    end     = date+datetime.timedelta(days=21)
    
    prev    = date-datetime.timedelta(days=1)
    next    = date+datetime.timedelta(days=1)
    
    weekday = date.weekday()
        
    return view(request, 'agenda', start, end, prev, next, weekday)