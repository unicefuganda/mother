from django.db import models

from rapidsms.models import ContactBase

from rapidsms.contrib.locations.models import Location

class MotherContact(models.Model):
    """
    This extension for Contacts allows developers to tie a Contact to
    whether they own their phone or not.
    """



    class Meta:
        abstract = True
