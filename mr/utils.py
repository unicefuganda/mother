from django.contrib.auth.models import User, Group
from django.conf import settings
from poll.models import Poll
from script.models import Script, ScriptStep
from script.utils.handling import find_best_response, find_closest_match
import traceback


def mr_autoreg(**kwargs):

    connection = kwargs['connection']
    progress = kwargs['sender']
    if not progress.script.slug == 'mr_autoreg':
        return

    session = ScriptSession.objects.filter(script=progress.script, connection=connection).order_by('-end_time')[0]
    script = progress.script

    role_poll = script.steps.get(order=1).poll
    district_poll = script.steps.get(order=2).poll
    subcounty_poll = script.steps.get(order=3).poll
    school_poll = script.steps.get(order=4).poll
    schools_poll = script.steps.get(order=5).poll
    name_poll = script.steps.get(order=6).poll

    if not connection.contact:
#            connection.contact = Contact.objects.create()
            connection.contact = EmisReporter.objects.create()
            connection.save
    contact = connection.contact

    subcounty = find_best_response(session, subcounty_poll)
    district = find_best_response(session, district_poll)

    if subcounty:
        subcounty = find_closest_match(subcounty, Location.objects.filter(type__name='sub_county'))

    if subcounty:
        contact.reporting_location = subcounty
    elif district:
        contact.reporting_location = district
    else:
        contact.reporting_location = Location.tree.root_nodes()[0]

    name = find_best_response(session, name_poll)
    if name:
        name = ' '.join([n.capitalize() for n in name.lower().split(' ')])
        contact.name = name[:100]

    if not contact.name:
        contact.name = 'Anonymous User'
    contact.save()

    reporting_school = None
    school = find_best_response(session, school_poll)
    if school:
        if subcounty:
            reporting_school = find_closest_match(school, School.objects.filter(location__name__in=[subcounty], \
                                                                                location__type__name='sub_county'), True)
        elif district:
            reporting_school = find_closest_match(school, School.objects.filter(location__name__in=[district.name], \
                                                                            location__type__name='district'), True)
        else:
            reporting_school = find_closest_match(school, School.objects.filter(location__name=Location.tree.root_nodes()[0].name))


models_created = []
structures_initialized = False


def init_structures(sender, **kwargs):
    global models_created
    global structures_initialized
    models_created.append(sender.__name__)
    required_models = ['eav.models', 'poll.models', 'script.models', 'django.contrib.auth.models']
    for required in required_models:
        if required not in models_created:
            return
    if not structures_initialized:
        init_autoreg(sender)
        structures_initialized = True


def init_autoreg(sender, **kwargs):
    script, created = Script.objects.get_or_create(
            slug="mrs_autoreg", defaults={
            'name':"Mother reminder autoregistration script"})
    if created:
        user, created = User.objects.get_or_create(username="admin")

        script.steps.add(ScriptStep.objects.create(
            script=script,
            message="Welcome message.",
            order=0,
            rule=ScriptStep.WAIT_MOVEON,
            start_offset=0,
            giveup_offset=60,
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
            order=1,
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
            order=2,
            rule=ScriptStep.RESEND_MOVEON,
            num_tries=1,
            start_offset=60,
            retry_offset=86400,
            giveup_offset=86400,
        ))
        script.steps.add(ScriptStep.objects.create(
            script=script,
            message="Congrats you're finished.",
            order=3,
            rule=ScriptStep.WAIT_MOVEON,
            start_offset=60,
            giveup_offset=0,
        ))

