from django.db import models
from organization.models import Organization
from helpdesk.models import Ticket
from django.contrib.auth.models import User

class TimeRegistration(models.Model):
    
    title   = models.CharField(max_length=255)
    start   = models.IntegerField()
    end     = models.IntegerField()
    
    user            = models.ForeignKey(User)
    organization    = models.ForeignKey(Organization)
    ticket          = models.ForeignKey(Ticket)