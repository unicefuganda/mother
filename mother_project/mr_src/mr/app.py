from rapidsms.apps.base import AppBase
from django.conf import settings
from script.models import Script, ScriptProgress
from rapidsms.models import Contact, Connection
from rapidsms_httprouter.models import Message
from datetime import datetime, timedelta
import re

class App (AppBase):
    def parse (self, message):
        for keywd in settings.KEYWORDS_AND_SLUGS:
            match = re.match(keywd, message.text)
            if match:
                if getattr(message, 'db_message', None):
                    message.db_message.text = message.text[len(match.group(0)):]
                    message.db_message.save()

    def handle (self, message):
        escargot = 'mrs_autoreg'
        match    = None
        for keywd in settings.KEYWORDS_AND_SLUGS:
            match = re.match(keywd, message.text, re.IGNORECASE)
            if match:
                escargot     = settings.KEYWORDS_AND_SLUGS[keywd]
                message.text = message.text[len(match.group(0)):]
                break
        if escargot == 'mrs_opt_out':
          if not message.connection.contact:
            # Stop sending you nothing? :-p
            return False
          sps = ScriptProgress.objects.filter(connection = message.connection)
          sps.delete()
          # ScriptProgress.objects.create(
          #     script = Script.objects.get(slug = escargot),
          # connection = message.connection)
          msg = Message(connection = message.connection, status = 'Q', direction = 'O', text = 'You will no longer receive FREE messages from the healthy mothers group. If you want to join again please send JOIN to 6400.')
          msg.save()
          return False
        if (not message.connection.contact) or (not ScriptProgress.objects.filter(connection = message.connection)):
            message.connection.contact = Contact.objects.create(name='Anonymous User')
            message.connection.contact.last_menses = datetime.now() - timedelta(days = 45)
            message.connection.contact.save()
            message.connection.save()
            ScriptProgress.objects.create(
                    script = Script.objects.get(slug = escargot),
                connection = message.connection)
            return False
        elif match and re.match(settings.KEYWORDS_AND_SLUGS['mrs_autoreg'], match.group(0), re.IGNORECASE):
          msg = Message(connection = message.connection, status = 'Q', direction = 'O', text = 'You are already a member of Mother Reminder. To restart, first send QUIT. Thank you!')
          msg.save()
        return False
