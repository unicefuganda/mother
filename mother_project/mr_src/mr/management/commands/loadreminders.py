"""
Load reminder messages into DB.
"""

from optparse import OptionParser, make_option

from django.test import TestCase
from django.contrib.auth.models import User, Group
from rapidsms.messages.incoming import IncomingMessage
from healthmodels.models import *
from rapidsms_httprouter.models import Message
from rapidsms.contrib.locations.models import Location, LocationType
import datetime
from rapidsms.models import Connection, Backend, Contact
from rapidsms.messages.incoming import IncomingMessage
from django.conf import settings
from script.utils.outgoing import check_progress
from script.models import Script, ScriptProgress, ScriptSession, ScriptResponse
from rapidsms_httprouter.router import get_router
from script.signals import script_progress_was_completed, script_progress
from poll.management import create_attributes

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

import sys

class Command(BaseCommand):
  option_list = BaseCommand.option_list + (
    make_option('-f', '--file', dest = 'file'),
  )

  def handle(self, **options):
    path  = options.get('file')
    if not path:
      raise ValueError, 'Provide a path with -f --file .'
    with open(path) as f:
      while True:
        try:
          x, y, week, day, z, a, b, text, c, d = f.readline().split('\t')
          text  = text[1:-1]
          rm  = None
          try:
            rm  = ReminderMessage.objects.get(week_number = int(week),
                                              day_number  = int(day))
            rm.reminder_text  = text
          except ReminderMessage.DoesNotExist:
            rm  = ReminderMessage(week_number   = int(week),
                                  day_number    = int(day),
                                  reminder_text = text)
          rm.save()
        except ValueError:
          break
        except StopIteration:
          break
