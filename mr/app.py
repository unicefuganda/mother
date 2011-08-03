from rapidsms.apps.base import AppBase
from django.conf import settings

class App (AppBase):

    def parse (self, message):
        message.text = message.text[:len(settings.SHORTCODE_PREFIX)]
        if getattr(message, 'db_message', None):
            message.db_message.text = message.db_message.text[len(settings.SHORTCODE_PREFIX):]
            message.db_message.save()

