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
    super(Sender, self).__init__()
    self.mothers = mums

  def run(self):
    while not self.mothers.empty():
      c, m = self.mothers.get()
      msg  = OutgoingMessage(c, m)
      msg.send()
      self.mothers.task_done()

class Command(BaseCommand):
  def handle(self, **options):
    for week in OUTGOING_MESSAGES.keys():
      this_week = OUTGOING_MESSAGES[week]
      for day in this_week.keys():
        mother_queue  = Queue.Queue()
        for mother in Contact.objects.raw('''
SELECT * FROM rapidsms_contact WHERE
  (last_menses + ('59 WEEK' :: INTERVAL)) :: DATE > NOW() :: DATE'''):
          mother_queue.put((mother.connection, 'If you want to stop receiving FREE messages from the healthy mothers group please reply with STOP.'))
        senders       = []
        for _ in range(os.getenv('SENDER_THREADS', 10)):
          sdr = Sender(mother_queue)
          sdr.start()
          senders.append(sdr)
        mother_queue.join()
        for t in senders:
          t.join()
