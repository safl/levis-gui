from django.db import models


class Organization(models.Model):
    """
    Abstract organizational entity.
    Other systems call this entity "Customer", "Site", "Department" etc.
    It is basicly just a unit which can be combined with other units
    to form a set of organizational relations.
    """
    
    name        = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    
    affiliate   = models.ManyToManyField('self')    # Related organizations
    
    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["-name"]
    
class Human(models.Model):
    """
    Human assets at the organization, usually just "Contacts" are stored.
    """
    
    name        = models.CharField(max_length=255)
    surname     = models.CharField(max_length=255)
    email       = models.CharField(max_length=255)
    phone       = models.CharField(max_length=255)    
    comments    = models.CharField(max_length=255)    
    
    organization = models.ManyToManyField(Organization)
    
    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["-name"]

class Address(models.Model):
    """Physical Address."""
    
    name    = models.CharField(max_length=255)
    
    street  = models.CharField(max_length=255)
    zip     = models.CharField(max_length=255)
    city    = models.CharField(max_length=255)
    
    organization = models.ForeignKey(Organization)
    
    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["-name"]

class File(models.Model):
    """
    Basic file-storage with organization-relation.
    Files are "versioned" by uploading a file with the same
    name and organization, a reference to the previous "version" is created.
    """
    
    name        = models.CharField(max_length=255)              # Metadata
    mime_type   = models.CharField(max_length=255)
    size        = models.IntegerField()
    modified    = models.DateTimeField()    
    description = models.CharField(max_length=255)
    
    blob = models.FileField(upload_to="files/%Y%m%d_%H_%M_%S")  # File content
    
    parent          = models.ForeignKey('self')
    organization    = models.ForeignKey(Organization)
    
    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["-name"]

class Note(models.Model):
    """
    Provide various notes / documentation about the organization which is
    not represented by any of the other models.
    """
    
    description = models.CharField(max_length=255)
    
    organization = models.ForeignKey(Organization)
    
class Domain(models.Model):
    """Domain names associated with customer."""
    
    name        = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    
    organization = models.ForeignKey(Organization)
    
    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["-name"]
    
class IpAlias(models.Model):
    """
    Provides a convenient alias for an ip-address, any where in the
    system where an ip-address is needed an alias can be used instead.
    
    Making it easier to manage a change such as the organizations public
    ip-address.
    """
    
    name        = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    
    address     = models.CharField(max_length=255)
    
    organization = models.ForeignKey(Organization)
    
    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["-name"]
    
class IpRangeAlias(models.Model):    
    """
    Provides a convenient alias for an ip-range, whenever an ip-range can
    be specified an IpRangeAlias can be used instead.
    
    Making it easier to manage a change such as the organizations local area
    network ranges.
    """
    
    name        = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    
    start_address   = models.CharField(max_length=255)
    end_address     = models.CharField(max_length=255)
    
    organization = models.ForeignKey(Organization)
    
    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["-name"]