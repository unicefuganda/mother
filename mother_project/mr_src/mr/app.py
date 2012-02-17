from rapidsms.apps.base import AppBase
from django.conf import settings
from script.models import Script, ScriptProgress
from rapidsms.models import Contact, Connection
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
        for keywd in settings.KEYWORDS_AND_SLUGS:
            match = re.match(keywd, message.text)
            if match:
                escargot     = settings.KEYWORDS_AND_SLUGS[keywd]
                message.text = message.text[len(match.group(0)):]
                break
        if (not message.connection.contact) or (not ScriptProgress.objects.filter(connection = message.connection)):
            message.connection.contact = Contact.objects.create(name='Anonymous User')
            message.connection.contact.last_menses = datetime.now() - timedelta(days = 45)
            message.connection.save()
            ScriptProgress.objects.create(
                    script = Script.objects.get(slug = escargot),
                connection = message.connection)
            return True
        return False
