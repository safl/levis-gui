from django.db import models
from django.contrib.auth.models import User

class State(models.Model):
    """Indication of ticket-state, is it new, open, closed?"""
    
    name        = models.CharField(max_length=10)
    description = models.CharField(max_length=50)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["-name"]
    
class Priority(models.Model):
    """
    Indication of how "urgent" a ticket is:
    
    very low, low, normal, high, very high
    """
    
    name        = models.CharField(max_length=10)
    description = models.CharField(max_length=50)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["-name"]

class Queue(models.Model):
    
    name        = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["-name"]

class Ticket(models.Model):
    
    number      = models.CharField(max_length=255)
    title       = models.CharField(max_length=255)
    
    created = models.IntegerField()
    
    state       = models.ForeignKey(State)
    priority    = models.ForeignKey(Priority)
    
    queue   = models.ForeignKey(Queue)    
    owner   = models.ForeignKey(User)
    
    def __unicode__(self):
        return str(self.number)
        
    class Meta:
        ordering = ["-number", "-created"]

class Article(models.Model):
    
    m_from  = models.CharField(max_length=255)
    m_to    = models.CharField(max_length=255)
    m_body  = models.TextField(max_length=1024)
    
    created = models.IntegerField()
    
    ticket  = models.ForeignKey(Ticket)

class Salutation(models.Model):
    
    salutation  = models.CharField(max_length=50)
    name        = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["-name"]

class Signature(models.Model):
    
    signature   = models.CharField(max_length=50)
    name        = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["-name"]

class Response(models.Model):
    
    name        = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["-name"]