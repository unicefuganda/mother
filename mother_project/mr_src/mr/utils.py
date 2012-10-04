# vim: ts=4
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.db import transaction
from poll.models import Poll
from script.models import Script, ScriptStep, ScriptSession, ScriptProgress
from script.utils.handling import find_best_response, find_closest_match
from rapidsms.models import Contact, Connection
from rapidsms.contrib.locations.models import Location, LocationType
from datetime import *
from healthmodels.models import HealthProvider, HealthFacility
import sys

def ascending_location_types(them = []):
  if not them:
    return ascending_location_types([Location.tree.root_nodes()[0].type])
  ndem  = Location.objects.filter(parent_type = them[-1])
  for it in ndem:
    return ascending_location_types(them + [it.type])
  return them

def mr_autoreg(**kwargs):
    connection = kwargs['connection']
    progress   = kwargs['sender']
    escargot   = progress.script.slug
    session = ScriptSession.objects.filter(script=progress.script, connection=connection).order_by('-end_time')[0]
    script = progress.script

    if escargot == 'mrs_opt_out':
        # ScriptProgress.objects.get(connection = connection).delete()
        # connection.delete()
        # Connection.objects.get(pk=connection.pk).delete()
        pass
    elif escargot == 'mrs_autoreg':
        location_poll   = script.steps.get(poll__name='mrs_location').poll
        locationcr_poll = script.steps.get(poll__name='mrs_location_corrector').poll
        menses_poll     = script.steps.get(poll__name='mrs_mensesweeks').poll
        visits_poll     = script.steps.get(poll__name='mrs_anc_visits').poll
        contact         = connection.contact
        contact.reporting_location = Location.tree.root_nodes()[0]
        locness = find_best_response(session, location_poll)
        if locness and locness.type.slug == 'district':
          contact.reporting_location = locness
        else:
          locness = find_best_response(session, locationcr_poll)
          if locness and locness.type.slug == 'district':
            contact.reporting_location = locness
          else:
            contact.reporting_location = find_best_response(session, location_poll) or find_best_response(session, locationcr_poll) or Location.tree.root_nodes()[0]
        #   TODO:   What to do for the names?
        last_menses = find_best_response(session, menses_poll)
        if last_menses:
            contact.last_menses = datetime.now() - timedelta(weeks = last_menses)
        else:
            contact.last_menses = datetime.now() - timedelta(days = 45)
        contact.anc_visits = find_best_response(session, visits_poll) or 0
        contact.save()
    elif escargot == 'mrs_hw_autoreg':
        district_poll = script.steps.get(poll__name='hw_district').poll
        hc_poll       = script.steps.get(poll__name='hw_healthcentre').poll
        hclevel_poll  = script.steps.get(poll__name='hw_hclevel').poll
        name_poll     = script.steps.get(poll__name='hw_name').poll

        #   TODO: Is this even legal in this country?
        contact, _ = HealthProvider.objects.get_or_create(pk = connection.contact.pk)
        try:
            place = find_best_response(session, district_poll)
            if not place: [][0]
            matching = Location.objects.filter(name__icontains = place,type="district")[0]
            contact.reporting_location = matching
        except IndexError:
            contact.reporting_location = Location.tree.root_nodes[0]
        name = find_best_response(session, name_poll)

        if name:
            name = ' '.join([n.capitalize() for n in name.lower().split(' ')])
            contact.name = name[:100]

        #   TODO: Tell Marcus the dox need to change to reflect this.
        #   Apparently, we need not bother with this.
        #   facility_type = HealthFacilityType()
        facility = HealthFacility(
                    #   TODO: Turn location into a Point.
                    #   location  = contact.reporting_location,
                    #       type  = facility_type,
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

def check_for_validity(progress):
  try:
    session       = ScriptSession.objects.filter(script = progress.script, connection = progress.connection, end_time = None)[0]
    location_poll = progress.script.steps.get(poll__name='mrs_location').poll
    loc           = find_best_response(session, location_poll)
    if not loc:
        return False
    elif loc.type.name != 'district':
        #find best response is not guaranteed to return a district in case name crashes
        dist_loc=loc.get_ancestors().filter(type="district")
        if dist_loc.exists():
            eav_obj=session.responses.filter(response__poll=location_poll).latest('response__date').response.eav
            eav_obj.poll_location_value=dist_loc[0]
            eav_obj.save()
            return True
    return loc.type.name  == 'district'
  except IndexError:
    pass
  return False

def validate_district(sender, **kwargs):
  thepoll = sender.step.poll
  if not thepoll or thepoll.name != 'mrs_location_corrector':
    return
  if not check_for_validity(sender):
    return
  sender.step = sender.script.steps.get(poll__name = 'mrs_mensesweeks')
  sender.save()

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
    script = None
    try:
        script  =   Script.objects.get(slug = 'mrs_opt_out')
        script.delete()
    except Script.DoesNotExist:
        pass
    # script = Script.objects.create(slug =   'mrs_opt_out',
    #                                name = "General opt-out script")
    # script.steps.add(ScriptStep.objects.create(
    #     script=script,
    #     message="You will no longer receive FREE messages from Mother Reminder. If you want to join again please send JOIN to 6400.",
    #     order=0,
    #     rule=ScriptStep.WAIT_MOVEON,
    #     start_offset=0,
    #     giveup_offset=60,
    # ))
    script = None
    try:
        script  =   Script.objects.get(slug = 'mrs_autoreg')
        script.delete()
    except Script.DoesNotExist:
        pass
    script  = Script.objects.create(slug = "mrs_autoreg",
                                    name = "Mother reminder autoregistration script")
    user, created = User.objects.get_or_create(username="admin")
    location_poll = Poll.objects.create
    script.steps.add(ScriptStep.objects.create(
        script  = script,
        message = "Thank you for joining Mother Reminder - a great way for fathers and mothers to get the information they need to have a healthy baby. All messages FREE!",
        order   = 0,
        rule    = ScriptStep.WAIT_MOVEON,
        start_offset  = 0,
        giveup_offset = 60,
    ))
    script.steps.add(ScriptStep.objects.create(
        script=script,
        poll=Poll.objects.create(
            user=user, \
            type=Poll.TYPE_LOCATION_DISTRICT, \
            name='mrs_location',
            question="Time to answer a few questions from Mother Reminder! Your response is FREE! From which district are you? Please reply with the name of your district only.",
            default_response='', \
        ),
        order=1,
        rule=ScriptStep.WAIT_MOVEON,
        start_offset=0,
        retry_offset=3600,
        num_tries=2,
        giveup_offset=3600 * 2,
    ))
    script.steps.add(ScriptStep.objects.create(
        script=script,
        poll=Poll.objects.create(
            user=user, \
            type=Poll.TYPE_LOCATION, \
            name='mrs_location_corrector',
            question="Mother Reminder didn't recognize your district. Please carefully type the name of your district and re-send.",
            default_response='', \
        ),
        order=2,
        rule=ScriptStep.WAIT_MOVEON,
        start_offset=0,
        retry_offset=3600,
        num_tries=1,
        giveup_offset=3600 * 2,
    ))
    script.steps.add(ScriptStep.objects.create(
        script=script,
        poll=Poll.objects.create(
            user=user,
            type=Poll.TYPE_NUMERIC,
            name='mrs_mensesweeks',
            question="Hello again from Mother Reminder! How long ago was the mother's last menses? Please reply with the number of weeks that have passed since the last menses.",
            default_response=''
        ),
        order=3,
        rule=ScriptStep.STRICT_MOVEON,
        start_offset=0,
        retry_offset=3600,
        num_tries=2,
        giveup_offset=3600 * 2,
    ))
    script.steps.add(ScriptStep.objects.create(
        script=script,
        poll=Poll.objects.create(
            user=user,
            type=Poll.TYPE_NUMERIC,
            name='mrs_anc_visits',
            question="You are almost there! One last question, how many times has the mother gone to the clinic during pregnancy? Please reply with the number of visits.",
            default_response=''
        ),
        order=4,
        rule=ScriptStep.STRICT_MOVEON,
        start_offset=0,
        retry_offset=3600,
        num_tries=2,
        giveup_offset=3600 * 2,
    ))
    script.steps.add(ScriptStep.objects.create(
        script=script,
        message='Thank you! You will now receive health information on your phone to help you and your family stay happy and healthy during pregnancy! All messages FREE!',
        rule=ScriptStep.WAIT_MOVEON,
        order=5,
        start_offset=0
    ))
    script = None
    try:
        script  =   Script.objects.get(slug = 'mrs_hw_autoreg')
        script.delete()
    except Script.DoesNotExist:
        pass
    script  = Script.objects.create(slug  =   "mrs_hw_autoreg",
                                    name  =   "Health worker auto-registration script.")
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
        retry_offset  = 3600,
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
        retry_offset    = 3600,
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
   retry_offset = 3600,
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
        start_offset    =   0,
        retry_offset    =   3600,
        giveup_offset   =   86400
    ))
    script.steps.add(ScriptStep.objects.create(
        script=script,
        message="You successfully registered as a Health Worker with Mother Reminder. You will be occasionally asked to provide certain information.",
        order=5,
        rule=ScriptStep.WAIT_MOVEON,
        start_offset=0,
        giveup_offset=0,
    ))
    if 'django.contrib.sites' in settings.INSTALLED_APPS:
        from django.contrib.sites.models import Site
        script.sites.add(Site.objects.get_current())
        for poll in Poll.objects.filter(user = user):
            poll.sites.add(Site.objects.get_current())

@transaction.commit_manually
def throw_down_scripts():
    'This is only for bad days. Like today.'
    ScriptSession.objects.all().delete()
    ScriptProgress.objects.all().delete()
    ScriptStep.objects.all().delete()
    Script.objects.all().delete()
    Poll.objects.all().delete()
    transaction.commit()
