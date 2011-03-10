from django.db import models

class Node(models.Model):
    
    name      = models.CharField(max_length=200)
    title     = models.CharField(max_length=255)
    content   = models.TextField()
    rendered  = models.TextField()
    is_dir    = models.IntegerField(max_length=1)
    date      = models.DateTimeField('Creation Date')
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["-name"]