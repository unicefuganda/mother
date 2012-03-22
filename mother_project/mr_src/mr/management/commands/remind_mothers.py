#!  /usr/bin/env python
# vim: ts=2
# encoding: UTF-8
from datetime import datetime, timedelta
import itertools
from django.db.models import Q
from django.core.management.base import BaseCommand
import os
import Queue
from rapidsms.models import Contact, Connection, Backend
from rapidsms_httprouter.models import Message
from rapidsms.messages.outgoing import OutgoingMessage
from mr.models import ReminderMessage
from script.models import ScriptProgress, Script
import threading

class Command(BaseCommand):
  def handle(self, **options):
    outmsgs = ReminderMessage.as_hash()
    for week in outmsgs.keys():
      this_week = outmsgs[week]
      for day in this_week.keys():
        mother_queue  = Queue.Queue()
        this_day      = this_week[day]
        # for mother in Contact.objects.filter(last_menses__range = (datetime.now() - timedelta(weeks = week, days = day), datetime.now())):
        for mother in Contact.objects.raw('''SELECT * FROM rapidsms_contact WHERE (last_menses + ('%d WEEK %d DAY' :: INTERVAL)) :: DATE = NOW() :: DATE''' % (week, day)):
          msg = Message(connection = mother.connection, status = 'Q', direction = 'O', text = this_day)
          msg.save()
