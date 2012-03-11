#!  /usr/bin/env python
# vim: ts=2
# Thread the sending of messages.
from datetime import datetime, timedelta
import itertools
from django.db.models import Q
from django.core.management.base import BaseCommand
from rapidsms.models import Contact, Connection, Backend
from rapidsms_httprouter.models import Message
from rapidsms.messages.outgoing import OutgoingMessage
from script.models import ScriptProgress, Script

OUTGOING_MESSAGES = {
  1: {
    1: 'Congratulations on your pregnancy! Have you gone to the clinic? You should be checked at least 4 times at a health centre to ensure a healthy pregnancy/baby.'
  }
}

class Command(BaseCommand):
  @transaction.commit_manually
  def handle(self, **options):
    for week in OUTGOING_MESSAGES.keys():
      this_week = OUTGOING_MESSAGES[week]
      for day in this_week.keys():
        for mother in Contact.objects.raw('''
SELECT * FROM rapidsms_contact WHERE
  (last_menses + ('%d WEEK %d DAY' :: INTERVAL)) :: DATE = NOW() :: DATE''' % (week, day)):
          this_day  = this_week[day]
          this_msg  = OutgoingMessage(mother.connection, this_day)
          this_msg.send()
