from rapidsms.apps.base import AppBase
from django.conf import settings
from script.models import Script, ScriptProgress
from rapidsms.models import Contact

class App (AppBase):

    def parse (self, message):
        message.text = message.text[:len(settings.SHORTCODE_PREFIX)]
        if getattr(message, 'db_message', None):
            message.db_message.text = message.db_message.text[len(settings.SHORTCODE_PREFIX):]
            message.db_message.save()

    def handle (self, message):
        if not message.connection.contact:
            message.connection.contact = Contact.objects.create(name='Anonymous User')
            message.connection.save()
            ScriptProgress.objects.create(script=Script.objects.get(slug="mrs_autoreg"), \
                                          connection=message.connection)
            return True
        return False
