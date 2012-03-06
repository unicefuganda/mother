"""
Basic tests for MRS
"""

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
from .utils import init_autoreg

class ModelTest(TestCase): #pragma: no cover
    def fake_incoming(self, message, connection=None):
        if connection is None:
            connection = self.connection
        router = get_router()
        router.handle_incoming(connection.backend.name, connection.identity, message)

    def spoof_incoming_obj(self, message, connection=None):
        if connection is None:
            connection = Connection.objects.all()[0]
        incomingmessage = IncomingMessage(connection, message)
        incomingmessage.db_message = Message.objects.create(direction='I', connection=Connection.objects.all()[0], text=message)
        return incomingmessage

    def assertResponseEquals(self, message, expected_response, connection=None):
        s = self.fake_incoming(message, connection)
        self.assertEquals(s.response, expected_response)

    def setUp(self):
        init_autoreg(None)
        # create_attributes()
        User.objects.get_or_create(username='admin')
        self.backend = Backend.objects.create(name='test')
        self.connection = Connection.objects.create(identity='8675309', backend=self.backend)
        country = LocationType.objects.create(name='country', slug='country')
        district = LocationType.objects.create(name='district', slug='district')
        subcounty = LocationType.objects.create(name='sub_county', slug='sub_county')
        self.root_node = Location.objects.create(type=country, name='Uganda')
        self.kampala_district = Location.objects.create(type=district, name='Kampala')
        self.kampala_subcounty = Location.objects.create(type=subcounty, name='Kampala')
        self.gulu_subcounty = Location.objects.create(type=subcounty, name='Gulu')

    def fake_script_dialog(self, script_prog, connection, responses, emit_signal=True):
        script = script_prog.script
        ss = ScriptSession.objects.create(script=script, connection=connection, start_time=datetime.datetime.now())
        for poll_name, resp in responses:
            poll = script.steps.get(poll__name=poll_name).poll
            poll.process_response(self.spoof_incoming_obj(resp))
            resp = poll.responses.all()[0]
            ScriptResponse.objects.create(session=ss, response=resp)
        if emit_signal:
            script_progress_was_completed.send(connection=connection, sender=script_prog)
        return ss

    def testBasicAutoReg(self):
        spc = ScriptProgress.objects.count()
        self.fake_incoming('mrs join')
        self.assertEquals(ScriptProgress.objects.count(), spc + 1)
        script_prog = ScriptProgress.objects.all()[0]
        self.assertEquals(script_prog.script.slug, "mrs_autoreg")
        cc = Contact.objects.count()
        self.fake_script_dialog(script_prog, Connection.objects.all()[0], [\
            ('mrs_district', 'Kampala'),
            ('mrs_menses', '1 month'),
            ('mrs_name', 'oh mother'),
            ('mrs_ownership', 'No'),
            ('mrs_visits', '27'),
        ])
        self.assertEquals(Contact.objects.count(), cc + 1)
        contact = Contact.objects.all()[0]
        self.assertEquals(contact.name, 'Oh Mother')
        self.assertEquals(contact.reporting_location, self.kampala_district)
        self.assertEquals(contact.owns_phone, False)
        self.assertEquals(contact.anc_visits, 27)

    def testHWAutoReg(self):
        spc = ScriptProgress.objects.count()
        self.fake_incoming('hw join')
        self.assertEquals(ScriptProgress.objects.count(), spc + 1)
        script_prog = ScriptProgress.objects.all()[0]
        self.assertEquals(script_prog.script.slug, "mrs_hw_autoreg")
        cc = Contact.objects.count()
        self.fake_script_dialog(script_prog, Connection.objects.all()[0], [\
            ('hw_district', 'Kampala'),
            ('hw_healthcentre', 'Kasubi'),
            ('hw_hclevel', 'hciv'),
            ('hw_name', 'David McCann')
        ])
        self.assertEquals(Contact.objects.count(), cc + 1)
        contact = Contact.objects.all()[0]
        self.assertEquals(contact.name, 'David Mccann')
        self.assertEquals(contact.reporting_location, self.kampala_district)

    def testBadAutoReg(self):
        """
        Crummy answers
        """
        pass
#        self.fake_incoming('join')
#        script_prog = ScriptProgress.objects.all()[0]
#        self.fake_script_dialog(script_prog, self.connection, [\
#            ('emis_role', 'bodaboda'), \
#            ('emis_district', 'kampala'), \
#            ('emis_subcounty', 'amudat'), \
#            ('emis_name', 'bad tester'), \
#        ])
#        self.assertEquals(EmisReporter.objects.count(), 1)
#        contact = EmisReporter.objects.all()[0]
#        self.assertEquals(contact.groups.all()[0].name, 'Other EMIS Reporters')
#        self.assertEquals(contact.reporting_location, self.kampala_district)

    def testAutoRegNoLocationData(self):
        pass
#        self.fake_incoming('join')
#        script_prog = ScriptProgress.objects.all()[0]
#        self.fake_script_dialog(script_prog, self.connection, [\
#            ('emis_role', 'teacher'), \
#            ('emis_name', 'no location data tester'), \
#        ])
#        self.assertEquals(EmisReporter.objects.count(), 1)
#        contact = EmisReporter.objects.all()[0]
#        self.assertEquals(contact.reporting_location, self.root_node)

    def testAutoRegNoRoleNoName(self):
        pass
#        self.fake_incoming('join')
#        script_prog = ScriptProgress.objects.all()[0]
#        self.fake_script_dialog(script_prog, self.connection, [\
#            ('emis_district', 'kampala'), \
#            ('emis_subcounty', 'Gul'), \
#            ('emis_one_school', 'St Marys'), \
#        ])
#        contact = EmisReporter.objects.all()[0]
#        self.assertEquals(contact.groups.all()[0].name, 'Other EMIS Reporters')
#        self.assertEquals(contact.reporting_location, self.gulu_subcounty)
#        self.assertEquals(contact.name, 'Anonymous User')

    def testChopKeyword(self):
        self.fake_incoming('mrs hi')
        self.assertEquals(Message.objects.all()[0].text, 'hi')

    def testDumpIntoAutoReg(self):
        self.fake_incoming('mrs join')
        self.assertEquals(ScriptProgress.objects.count(), 1)
        self.fake_incoming('mrs join')
        self.assertEquals(ScriptProgress.objects.count(), 1)
