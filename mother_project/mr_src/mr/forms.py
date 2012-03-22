#!/usr/bin/python
# -*- coding: utf-8 -*-
from django import forms
from rapidsms.models import Contact, Connection
from django.core.paginator import Paginator, Page
from django.contrib.auth.models import Group
from django.db.models import Q
from rapidsms_httprouter.router import get_router, \
    start_sending_mass_messages, stop_sending_mass_messages
from rapidsms_httprouter.models import Message
from rapidsms.messages.outgoing import OutgoingMessage
from generic.forms import ActionForm, FilterForm
from contact.models import MassText, Flag
from django.contrib.sites.models import Site
from rapidsms.contrib.locations.models import Location
from uganda_common.forms import SMSInput
from django.conf import settings
import datetime
from rapidsms_httprouter.models import Message
from django.forms.util import ErrorList
from mr.models import ReminderMessage

class ReminderMessageForm(ActionForm):
    'For ReminderMessage, does the C and  D of CRUD.'
    week    = forms.IntegerField(help_text = '(the week in which this reminder should be sent)')
    day     = forms.IntegerField(help_text = '(the day in the week on which this reminder should be sent)')
    message = forms.CharField(widget = SMSInput())
    action_label  = 'Record New Reminder Message'

    def perform(self, request, results):
      rmdr  = ReminderMessage(week_number = self.cleaned_data['week'],
                              day_number  = self.cleaned_data['day'],
                            reminder_text = self.cleaned_data['message'])
      rmdr.save()
      return ('Saved reminder message for week %d, day %d' % (rmdr.week_number, rmdr.day_number), 'successfully.')
