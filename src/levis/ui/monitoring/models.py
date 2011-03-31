from django.db import models

class Device(models.Model):
    
    name        = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    
    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["-name"]

class Credential(models.Model):
    
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    domain   = models.CharField(max_length=255)
    type     = models.CharField(max_length=10)

class Eventlog(models.Model):
    pass