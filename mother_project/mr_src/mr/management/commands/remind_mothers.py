#!  /usr/bin/env python
# encoding: UTF-8
# vim: ts=2
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

class Command(BaseCommand):
  def handle(self, **options):
    outmsgs = ReminderMessage.as_hash()
    for week in outmsgs.keys():
      this_week = outmsgs[week]
      for day in this_week.keys():
        mother_queue  = Queue.Queue()
        this_day      = this_week[day]
        # for mother in Contact.objects.raw('''SELECT * FROM rapidsms_contact WHERE (last_menses + ('%d WEEK %d DAY' :: INTERVAL)) :: DATE = NOW() :: DATE''' % (week, day)):
        # Because Django ORM speaks pidgin: “today” will be encoded as “between end of yesterday and start of tomorrow”. Hahaha. As long as it is not SQL.
        back_then = datetime.now() - timedelta(weeks = week, days = day)
        prior_day = back_then - timedelta(days = 1)
        for mother in Contact.objects.filter(last_menses__range = (prior_day, back_then)):
          msg = Message(connection = mother.connection, status = 'Q', direction = 'O', text = this_day)
          msg.save()
