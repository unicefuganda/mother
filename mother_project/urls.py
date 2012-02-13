from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
#from rapidsms_xforms.urls import urlpatterns as xforms_urls
#from rapidsms_backendmanager.urls import urlpatterns as backendmgr_urls
from rapidsms_httprouter.urls import urlpatterns as router_urls
from rapidsms_httprouter.views import receive, console
from rapidsms.models import Contact
from healthmodels.urls import urlpatterns as healthmodels_urls
from healthmodels.models import HealthProvider, HealthFacility
from contact.urls import urlpatterns as contact_urls
from generic.views import generic
from generic.sorters import SimpleSorter
from rapidsms_httprouter.models import Message
from contact.forms import FreeSearchTextForm, FreeSearchForm, DistictFilterMessageForm, ReplyTextForm, DistictFilterForm, MassTextForm
from contact.views import view_message_history
from mr.views import view_mother
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic.simple import direct_to_template
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^my-project/', include('my_project.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^admin/', include(admin.site.urls)),

    # RapidSMS core URLs
    (r'^account/', include('rapidsms.urls.login_logout')),
    url(r'^$', direct_to_template, {'template': 'mr/index.html'}, name="rapidsms-dashboard"),
    url('^accounts/login', 'rapidsms.views.login'),
    url('^accounts/logout', 'rapidsms.views.logout'),
    # RapidSMS contrib app URLs
    url(r'^contact/messagelog/$', login_required(generic), {
      'model':Message,
      'filter_forms':[FreeSearchTextForm, DistictFilterMessageForm],
      'action_forms':[ReplyTextForm],
      'objects_per_page':25,
      'partial_row':'mr/partials/message_row.html',
      'base_template':'contact/messages_base.html',
      'columns':[('Text', True, 'text', SimpleSorter()),
                 ('Contact Information', True, 'connection__contact__name', SimpleSorter(),),
                 ('Date', True, 'date', SimpleSorter(),),
                 ('Type', True, 'application', SimpleSorter(),),
                 ('Response', False, 'response', None,),
                 ],
      'sort_column':'date',
      'sort_ascending':False,
    }, name="contact-messagelog"),
    url(r'^reporter/$', login_required(generic), {
        'model':Contact,
        'results_title':'Mothers',
        'filter_forms':[FreeSearchForm, DistictFilterForm],
        'action_forms':[MassTextForm],
        'objects_per_page':25,
        'partial_row':'mr/partials/mother_row.html',
        'columns':[('Name', True, 'name', SimpleSorter()),
                 ('Number', True, 'connection__identity', SimpleSorter(),),
                 ('District', True, 'reporting_location__name', SimpleSorter(),),
                 ('Owns Phone?', True, 'owns_phone', SimpleSorter()),
                 ('Last Menses', True, 'last_menses', SimpleSorter()),
                 ('ANC Visits', True, 'anc_visits', SimpleSorter())],
        'sort_column':'name',
        'sort_ascending':True,
    }, name="mrs-contact"),
    url(r'^healthworker/$', login_required(generic), {
        'model':HealthProvider,
        'results_title':'Health Workers',
        'filter_forms':[FreeSearchForm, DistictFilterForm],
        'action_forms':[MassTextForm],
        'objects_per_page':25,
        'partial_row':'mr/partials/hw_row.html',
        'columns':[('Name', True, 'name', SimpleSorter()),
                  ('Health Centre', True, 'facility', SimpleSorter()),
                 ('Number', True, 'connection__identity', SimpleSorter(),),
                 ('District', True, 'reporting_location__name', SimpleSorter(),),
                 ],
        'sort_column':'name',
        'sort_ascending':True,
    }, name="hw-contact"),
    url(r'^clinic/$', login_required(generic), {
        'model':HealthFacility,
        'results_title':'Health Facility',
        'filter_forms':[FreeSearchForm, DistictFilterForm],
        # 'action_forms':[MassTextForm],
        'objects_per_page':25,
        'partial_row':'mr/partials/clinic_row.html',
        'columns':[('Name', True, 'name', SimpleSorter()),
                  ('Location', True, 'reporting_location__name', SimpleSorter()),
                 ('Type', True, 'type__name', SimpleSorter(),),
                 ],
        'sort_column':'name',
        'sort_ascending':True,
    }, name="hw-clinic"),
    url(r"^contact/(\d+)/message_history/$", view_message_history, name="message_history"),
    url(r"^(\d+)/view/$", view_mother),
    url("^router/receive", receive),
    url("^router/console", staff_member_required(console), {}, 'httprouter-console'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        # helper URLs file that automatically serves the 'static' folder in
        # INSTALLED_APPS via the Django static media server (NOT for use in
        # production)
        (r'^', include('rapidsms.urls.static_media')),
    )


from urllib import quote_plus
from urllib2 import urlopen
from urlparse import urlparse, parse_qs
from django.conf import settings

# monkey patch rapidsms_httprouter to use POST instead GET
def fetch_url(router, url):

    # no url, means console, return success
    if not url:
        return 200

    # parse our url, grabbing
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    # first try posting to our primary URL
    try:
        # first try posting to our primary URL
        url = settings.YO_PRIMARY_URL + "?" + parsed.query
        router.info("YO URL: " + url)
        response = urlopen(url)

        # if that worked, hurry, return the code
        if response.getcode() == 200:
            body = response.read()
            router.info("YO: " + body)
            # if they said this was ok, return so
            if body.find('OK') >= 0:
                return response.getcode()

    except Exception as e:
        router.error("Unable to send message, got error.", exc_info=True)
        return 200

    # next try the secondary url
    try:
        url = settings.YO_SECONDARY_URL + "?" + parsed.query
        router.info("SECONDARY URL: " + url)
        response = urlopen(url)

        # read the body
        body = response.read()
        router.info("YO (RETRY): " + body)
        # if they said this was ok, return so
        if body.find('OK') >= 0:
            return response.getcode()

    except Exception as e:
        router.error("Unable to send message, got error.", exc_info=True)
        return 200


from rapidsms_httprouter.router import get_router
get_router(start_workers=True)


