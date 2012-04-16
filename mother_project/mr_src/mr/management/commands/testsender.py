"""
Basic tests for MRS
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
    make_option('-n', '--number', dest = 'num'),
    make_option('-t', '--text', dest = 'text')
  )

  def handle(self, **options):
    if len(sys.argv) < 2:
      sys.stderr.write('number message\n')
      sys.exit(1)
    con, _ = Connection.objects.get_or_create(identity  = options.get('num', '256772344681'),
                                            backend  = Backend.objects.get_or_create(name = 'TestBackend')[0])
    r   = get_router()
    r.handle_incoming(con.backend.name, con.identity, options.get('text', 'EMPTY'))
