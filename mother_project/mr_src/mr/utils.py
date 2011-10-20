# vim: ts=4
from .models import HealthProvider, HealthFacility
from django.contrib.auth.models import User, Group
from django.conf import settings
from poll.models import Poll
from script.models import Script, ScriptStep, ScriptSession
from script.utils.handling import find_best_response, find_closest_match
from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Location
from datetime import *
from healthmodels.models import HealthProvider, HealthFacility

def mr_autoreg(**kwargs):

    connection = kwargs['connection']
    progress   = kwargs['sender']
    escargot   = progress.script.slug
    session = ScriptSession.objects.filter(script=progress.script, connection=connection).order_by('-end_time')[0]
    script = progress.script

    if escargot == 'mrs_autoreg':
        district_poll = script.steps.get(poll__name='mrs_district').poll
        ownership_poll = script.steps.get(poll__name='mrs_ownership').poll
        menses_poll = script.steps.get(poll__name='mrs_menses').poll
        visits_poll = script.steps.get(poll__name='mrs_visits').poll
        name_poll = script.steps.get(poll__name='mrs_name').poll

        contact = connection.contact
    
        contact.reporting_location = find_best_response(session, district_poll) or Location.tree.root_nodes()[0]

        name = find_best_response(session, name_poll)
        if name:
            name = ' '.join([n.capitalize() for n in name.lower().split(' ')])
            contact.name = name[:100]

        resps = session.responses.filter(response__poll=ownership_poll, \
                                     response__has_errors=False).order_by('-response__date')
        if resps.count() and resps[0].response.categories.filter(category__name='no').count():
            contact.owns_phone = False

        last_menses = find_best_response(session, menses_poll)
        if last_menses:
            contact.last_menses = datetime.now() - timedelta(last_menses)

        contact.anc_visits = find_best_response(session, visits_poll) or 0
        contact.save()

    elif escargot == 'mrs_hw_autoreg':
        district_poll = script.steps.get(poll__name='hw_district').poll
        hc_poll = script.steps.get(poll__name='hw_healthcentre').poll
        hclevel_poll = script.steps.get(poll__name='hw_hclevel').poll
        name_poll = script.steps.get(poll__name='hw_name').poll

        contact = HealthProvider.objects.get(pk = connection.contact.pk)

        #   contact.location = find_best_response(session, district_poll) or Location.tree.root_nodes()[0]
        contact.reporting_location = find_best_response(session, district_poll) or Location.tree.root_nodes()[0]

        name = find_best_response(session, name_poll)

        if name:
            name = ' '.join([n.capitalize() for n in name.lower().split(' ')])
            contact.name = name[:100]

        #   TODO: Tell Marcus the dox need to change to reflect this.
        #   Apparently, we need not bother with this.
        #   facility_type = HealthFacilityType()
        facility = HealthFacility(
                    location  = contact.reporting_location,
                        type  = facility_type,
                        name  = find_best_response(session, hc_poll))
        contact.facility = facility
        contact.save()
    elif escargot == 'mrs_hw_reminder':
        qn1 = script.steps.get(poll__name = 'hw_question_1').poll
        qn2 = script.steps.get(poll__name = 'hw_question_2').poll
        qn3 = script.steps.get(poll__name = 'hw_question_3').poll
        qn4 = script.steps.get(poll__name = 'hw_question_4').poll

        contact     = HealthProvider.objects.get(pk = connection.contact.pk)
        first_anc   = find_best_response(session, qn1)
        fourth_anc  = find_best_response(session, qn2)
        art_treated = find_best_response(session, qn3)
        hiv_diag    = find_best_response(session, qn4)

        questionnaire = Questionnaire(
            health_worker   = contact,
            first_anc_visit = first_anc,
           fourth_anc_visit = fourth_anc,
           art_treated_mums = art_treated,
           six_month_hiv_diag = hiv_diag)
        questionnaire.save()

required_models = ['eav.models', 'poll.models', 'script.models', 'django.contrib.auth.models']

def init_structures(sender, **kwargs):
    global required_models
    if not required_models:
        return
    try:
        required_models.remove(sender.__name__)
        if not required_models:
            init_autoreg(sender)
    except ValueError:
        pass

def init_autoreg(sender, **kwargs):
    script, created = Script.objects.get_or_create(
            slug="mrs_autoreg", defaults={
            'name':"Mother reminder autoregistration script"})
    if created:
        user, created = User.objects.get_or_create(username="admin")

        script.steps.add(ScriptStep.objects.create(
            script=script,
            message="Welcome to the Mother Reminder registration. Please answer the questions in the following messages.",
            order=0,
            rule=ScriptStep.WAIT_MOVEON,
            start_offset=0,
            giveup_offset=60,
        ))
        own_poll = Poll.objects.create(
            user=user, \
            type=Poll.TYPE_TEXT, \
            name='mrs_ownership',
            question='Does the mother own this phone?', \
            default_response='', \
        )
        own_poll.add_yesno_categories()
        script.steps.add(ScriptStep.objects.create(
            script=script,
            poll=own_poll,
            order=1,
            rule=ScriptStep.STRICT_MOVEON,
            start_offset=0,
            retry_offset=86400,
            num_tries=1,
            giveup_offset=86400,
        ))
        district_poll = Poll.objects.create(
            user=user, \
            type='district', \
            name='mrs_district',
            question='What is the name of your district?', \
            default_response='', \
        )
        script.steps.add(ScriptStep.objects.create(
            script=script,
            poll=district_poll,
            order=2,
            rule=ScriptStep.STRICT_MOVEON,
            start_offset=0,
            retry_offset=86400,
            num_tries=1,
            giveup_offset=86400,
        ))
        menses_poll = Poll.objects.create(
            user=user, \
            type='timedelt', \
            name='mrs_menses',
            question='How long has it been since your last menses?', \
            default_response='', \
        )
        script.steps.add(ScriptStep.objects.create(
            script=script,
            poll=menses_poll,
            order=3,
            rule=ScriptStep.STRICT_MOVEON,
            start_offset=0,
            retry_offset=86400,
            num_tries=1,
            giveup_offset=86400,
        ))
        visits_poll = Poll.objects.create(
            user=user, \
            type=Poll.TYPE_NUMERIC, \
            name='mrs_visits',
            question='How many visits to your health provider have you made?', \
            default_response='', \
        )
        script.steps.add(ScriptStep.objects.create(
            script=script,
            poll=visits_poll,
            order=4,
            rule=ScriptStep.STRICT_MOVEON,
            start_offset=0,
            retry_offset=86400,
            num_tries=1,
            giveup_offset=86400,
        ))
        name_poll = Poll.objects.create(
            user=user, \
            type=Poll.TYPE_TEXT, \
            name='mrs_name',
            question='What is your name?', \
            default_response='', \
        )
        script.steps.add(ScriptStep.objects.create(
            script=script,
            poll=name_poll,
            order=5,
            rule=ScriptStep.RESEND_MOVEON,
            num_tries=1,
            start_offset=60,
            retry_offset=86400,
            giveup_offset=86400,
        ))
        script.steps.add(ScriptStep.objects.create(
            script=script,
            message="You successfully registered the pregnancy with Mother Reminder.You will be sent important information about your pregnancy and reminders for checkups.",
            order=6,
            rule=ScriptStep.WAIT_MOVEON,
            start_offset=60,
            giveup_offset=0,
        ))
        if 'django.contrib.sites' in settings.INSTALLED_APPS:
            from django.contrib.sites.models import Site
            script.sites.add(Site.objects.get_current())
            for poll in [district_poll, name_poll, menses_poll, visits_poll, own_poll]:
                poll.sites.add(Site.objects.get_current())
    script, created  = Script.objects.get_or_create(
            slug="mrs_hw_autoreg", defaults={
            'name':"Health worker auto-registration script."})
    if created:
        user, created = User.objects.get_or_create(username="admin")

        script.steps.add(ScriptStep.objects.create(
            script=script,
            message="Welcome to the Health Worker registration for Mother Reminder. Please answer the questions in the following messages.",
            order=0,
            rule=ScriptStep.WAIT_MOVEON,
            start_offset=0,
            giveup_offset=60,
        ))
        script.steps.add(ScriptStep.objects.create(
            script = script,
            poll   = Poll.objects.create(user = user, type = Poll.TYPE_TEXT,
                        name     = 'hw_district',
                        question = 'What is the name of your district?',
                default_response = ''),
            order         = 1,
            rule          = ScriptStep.STRICT_MOVEON,
            start_offset  = 0,
            retry_offset  = 86400,
            num_tries     = 1,
            giveup_offset = 86400
        ))
        script.steps.add(ScriptStep.objects.create(
            script = script,
            poll   = Poll.objects.create(user = user, type = Poll.TYPE_TEXT,
                            name = 'hw_healthcentre',
                        question = 'What is the name of your Health Centre?',
                default_response = ''),
            order           = 2,
            rule            = ScriptStep.STRICT_MOVEON,
            start_offset    = 0,
            retry_offset    = 86400,
            num_tries       = 1,
            giveup_offset   = 86400
        ))
        script.steps.add(ScriptStep.objects.create(
            script  = script,
               poll = Poll.objects.create(user = user, type = Poll.TYPE_TEXT,
                        name = 'hw_hclevel',
                    question = 'What is the level of your Health Centre?',
            default_response = ''),
              order = 3,
               rule = ScriptStep.STRICT_MOVEON,
       start_offset = 0,
       retry_offset = 86400,
          num_tries = 1,
      giveup_offset = 86400
        ))
        script.steps.add(ScriptStep.objects.create(
            script  =   script,
            poll    =   Poll.objects.create(user=user, type=Poll.TYPE_TEXT,
                        name    =   'hw_name',
                    question    =   'What is your name?',
            default_response    =   ''
        ),
            order           =   4,
            rule            =   ScriptStep.RESEND_MOVEON,
            num_tries       =   1,
            start_offset    =   60,
            retry_offset    =   86400,
            giveup_offset   =   86400
        ))
        script.steps.add(ScriptStep.objects.create(
            script=script,
            message="You successfully registered as a Health Worker with Mother Reminder. You will be occasionally asked to provide certain information.",
            order=5,
            rule=ScriptStep.WAIT_MOVEON,
            start_offset=60,
            giveup_offset=0,
        ))
        if 'django.contrib.sites' in settings.INSTALLED_APPS:
            from django.contrib.sites.models import Site
            script.sites.add(Site.objects.get_current())
            for poll in Poll.objects.filter(user = user):
                poll.sites.add(Site.objects.get_current())
    script, created  = Script.objects.get_or_create(
            slug="mrs_hw_reminder", defaults={
            'name':"Health worker reminder script."})
    if created:
        user, created = User.objects.get_or_create(username="admin")

        script.steps.add(ScriptStep.objects.create(
            script = script,
            poll   = Poll.objects.create(user = user, type = Poll.TYPE_NUMERIC,
                        name     = 'hw_question_1',
                        question = 'How many women came for their first ANC visit this month?',
                default_response = ''),
            order         = 0,
            rule          = ScriptStep.STRICT_MOVEON,
            start_offset  = 0,
            retry_offset  = 86400 * 2,
            num_tries     = 7,
            giveup_offset = 86400 * 15
        ))
        script.steps.add(ScriptStep.objects.create(
            script = script,
            poll   = Poll.objects.create(user = user, type = Poll.TYPE_NUMERIC,
                        name     = 'hw_question_2',
                        question = 'How many women came for their fourth ANC visit this month?',
                default_response = ''),
            order         = 1,
            rule          = ScriptStep.STRICT_MOVEON,
            start_offset  = 0,
            retry_offset  = 86400 * 2,
            num_tries     = 7,
            giveup_offset = 86400 * 15
        ))
        script.steps.add(ScriptStep.objects.create(
            script = script,
            poll   = Poll.objects.create(user = user, type = Poll.TYPE_NUMERIC,
                        name     = 'hw_question_3',
                        question = 'How many HIV+ mothers are receiving anti-retroviral treatment?',
                default_response = ''),
            order         = 2,
            rule          = ScriptStep.STRICT_MOVEON,
            start_offset  = 0,
            retry_offset  = 86400 * 2,
            num_tries     = 7,
            giveup_offset = 86400 * 15
        ))
        script.steps.add(ScriptStep.objects.create(
            script = script,
            poll   = Poll.objects.create(user = user, type = Poll.TYPE_NUMERIC,
                        name     = 'hw_question_4',
                        question = 'How many infants returned for 6-week checkup for early infant HIV diagnosis?',
                default_response = ''),
            order         = 3,
            rule          = ScriptStep.STRICT_MOVEON,
            start_offset  = 0,
            retry_offset  = 86400 * 2,
            num_tries     = 7,
            giveup_offset = 86400 * 15
        ))
        script.steps.add(ScriptStep.objects.create(
            script=script,
            message="Thank you for sending us that information.",
            order=4,
            rule=ScriptStep.WAIT_MOVEON,
            start_offset=60,
            giveup_offset=0,
        ))
        if 'django.contrib.sites' in settings.INSTALLED_APPS:
            from django.contrib.sites.models import Site
            script.sites.add(Site.objects.get_current())
            for poll in Poll.objects.filter(user = user):
                poll.sites.add(Site.objects.get_current())



def reminders(last_menses):
    toret = []
    if last_menses:
        offset = timedelta(90)
        curtime = last_menses + offset
        for m in ["It's time for your first trimester visit!", "It's time for your second trimester visit!", "It's time for your third trimester visit!", "Please see your doctor for antenatal care"]:
            toret.append((curtime, m,))
            curtime = curtime + offset
    return toret
