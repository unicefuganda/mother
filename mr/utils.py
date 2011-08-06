from django.contrib.auth.models import User, Group
from django.conf import settings
from poll.models import Poll
from script.models import Script, ScriptStep, ScriptSession
from script.utils.handling import find_best_response, find_closest_match
from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Location
import datetime
import traceback


def mr_autoreg(**kwargs):

    connection = kwargs['connection']
    progress = kwargs['sender']
    if not progress.script.slug == 'mrs_autoreg':
        return

    session = ScriptSession.objects.filter(script=progress.script, connection=connection).order_by('-end_time')[0]
    script = progress.script

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
        contact.last_menses = datetime.datetime.now() - datetime.timedelta(last_menses)

    contact.anc_visits = find_best_response(session, visits_poll) or 0
    contact.save()


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
        if 'django.contrib.sites' in settings.INSTALLED_APPS:
            from django.contrib.sites.models import Site
            script.sites.add(Site.objects.get_current())
        user, created = User.objects.get_or_create(username="admin")

        script.steps.add(ScriptStep.objects.create(
            script=script,
            message="Welcome to the demo of Mother Reminder. Please answer the questions in the following messages.",
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
            question='When was your last menses?', \
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
            for poll in [district_poll, name_poll, menses_poll, visits_poll, own_poll]:
                poll.sites.add(Site.objects.get_current())


def reminders(last_menses):
    offset = datetime.timedelta(90)
    curtime = last_menses + offset
    toret = []
    if last_menses:
        for m in ["It's time for your first trimester visit!", "It's time for your second trimester visit!", "It's time for your third trimester visit!", "Please see your doctor for antenatal care"]:
            toret.append((curtime, m,))
            curtime = curtime + offset
    return toret
