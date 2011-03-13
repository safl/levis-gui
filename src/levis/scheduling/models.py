from django.db import models
from django.contrib.auth.models import User
from organization.models import Organization, Address

import datetime

class Type(models.Model):
       
    name        = models.CharField(max_length=10)
    description = models.CharField(max_length=50)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["-name"]

class Exception(models.Model):
    
    date = models.DateField()

class Frequency(models.Model):
    
    name = models.CharField(max_length=10)
    description = models.CharField(max_length=50)
    
    def __unicode__(self):
        return self.name

class Event(models.Model):
    """
    The following describes how the calendar representation
    should be interpreted.
    
    SINGULAR - Occurs only once, einmal ist keinmal...
    
        INTERVAL:
            Ignored / null.
    
    DAILY - Occurs everyday (mon, tue, wed, fri, sat, sun)
        
        DAYS:
            Fixed to 1.
        
        INTERVAL:
            - ignored        
            
    WEEKLY - Occurs every week on one or more days in the week:
        
        DAYS:
            User defined, must contain one or more weekdays.
        
        INTERVAL:
            - 1: Every week
            - 2: Every second week
            - 3: Every third week
            
    MONTHLY_BY_DOM - Occurs every month on a specific day/date in the month:
        
        DAYS:
            Ignored.
        
        INTERVAL:
            - 1-31: Day of the month
        
    MONTHY_BY_DOW - Occurs every month on a specific weekday:
        
        DAYS:
            User defined, must contain exactly one day.
        
        INTERVAL:
            - 1: First 'Wednesday' in every month.
            - 2: Second 'Wednesday' in every month.
            - 3: Third 'Wednesday' in every month.
            - 4: Last 'Wednesday' in every month.
    
    """
    
    description = models.CharField(max_length=255)
    
    date_start   = models.DateField(default=datetime.date.today)
    date_end     = models.DateField(default=datetime.date.today, null=True, blank=True)
    
    time_start  = models.TimeField()
    time_end    = models.TimeField()
    
    frequency   = models.ForeignKey(Frequency)
    interval    = models.IntegerField(default=0)
    
    mon = models.IntegerField(default=0)
    tue = models.IntegerField(default=0)
    wed = models.IntegerField(default=0)
    thu = models.IntegerField(default=0)
    fri = models.IntegerField(default=0)
    sat = models.IntegerField(default=0)
    sun = models.IntegerField(default=0)
    
    user    = models.ForeignKey(User)
    type    = models.ForeignKey(Type)
    
    def __unicode__(self):
        return self.description
    
    class Meta:
        ordering = ["-date_start"]