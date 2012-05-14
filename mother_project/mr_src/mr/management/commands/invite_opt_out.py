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

class Command(BaseCommand):
    def handle(self, **options):
        outmsgs = ReminderMessage.as_hash().keys()
        outmsgs.sort()
        try:
            lastweek = outmsgs[-1]

            for mother in Contact.objects.filter(interested=True,
                last_menses__lt=(datetime.now() - timedelta(weeks=lastweek))).exclude(connection=None):
                text = 'If you want to stop receiving FREE messages from Mother Reminder please reply with STOP.'
                last_optout = Message.objects.filter(connection=mother.default_connection).filter(text=text).order_by('-date')
                if not last_optout:
                    msg = Message.objects.create(connection=mother.default_connection, direction='O', status='Q',
                        text=text)
                else:
                    if last_optout[0].date + timedelta(weeks=8) <= datetime.now():
                        msg = Message.objects.create(connection=mother.default_connection, direction='O', status='Q',
                            text=text)

                        # msg.save()
                        # application, batch, connection, date, direction, flags, id, in_response_to, poll, poll_responses, priority, responses, status, submissions, text
        except IndexError:
            pass
