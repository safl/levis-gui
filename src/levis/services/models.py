from django.db import models

class MailAccountType(models.Model):
    
    name        = models.CharField(max_length=10)
    description = models.CharField(max_length=50)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["-name"]

class MailAccount(models.Model):
       
    name        = models.CharField(max_length=10)
    description = models.CharField(
        max_length  = 50,
        blank       = True
    )
    
    hostname    = models.CharField(max_length=255)
    port        = models.IntegerField()
    use_ssl     = models.BooleanField()
    
    username    = models.CharField(max_length=255)
    password    = models.CharField(max_length=255)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["-name"]