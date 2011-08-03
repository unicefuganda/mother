from django.db import models
from rapidsms.models import ContactBase

class MotherContact(models.Model):
    """
    This extension for Contacts allows developers to tie a Contact to
    whether they own their phone or not, and also the last date of menstruation.
    """
    owns_phone = models.BooleanField(default=True)
    last_menses = models.DateTimeField(null=True)
    anc_visits = models.IntegerField(null=True)

    class Meta:
        abstract = True
