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
from .reminders import OUTGOING_MESSAGES
from script.models import ScriptProgress, Script
import threading

class Sender(threading.Thread):
  def __init__(self, mums):
    self.mothers = mums

  def run(self):
    while not self.mothers.empty():
      c, m = self.mothers.get()
      msg  = OutgoingMessage(c, m)
      msg.send()
      self.mothers.task_done()

class Command(BaseCommand):
  @transaction.commit_manually
  def handle(self, **options):
    for week in OUTGOING_MESSAGES.keys():
      this_week = OUTGOING_MESSAGES[week]
      for day in this_week.keys():
        mother_queue  = Queue.Queue()
        this_day      = this_week[day]
        for mother in Contact.objects.raw('''
SELECT * FROM rapidsms_contact WHERE
  (last_menses + ('%d WEEK %d DAY' :: INTERVAL)) :: DATE = NOW() :: DATE''' % (week, day)):
          mother_queue.put((mother.connection, this_day))
        senders       = []
        for _ in range(os.getenv('SENDER_THREADS', 10)):
          sdr = Sender(mother_queue)
          sdr.start()
          senders.append(sdr)
        mother_queue.join()
        for t in senders:
          t.join()
