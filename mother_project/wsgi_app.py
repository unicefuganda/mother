import sys, os

filedir = os.path.dirname(__file__)
sys.path.append(os.path.join(filedir))

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import sys

from django.core.handlers.wsgi import WSGIHandler

application = WSGIHandler()
