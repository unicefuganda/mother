from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
#from rapidsms_xforms.urls import urlpatterns as xforms_urls
#from rapidsms_backendmanager.urls import urlpatterns as backendmgr_urls
from rapidsms_httprouter.urls import urlpatterns as router_urls
from healthmodels.urls import urlpatterns as healthmodels_urls
from contact.urls import urlpatterns as contact_urls
from generic.views import generic
from generic.sorters import SimpleSorter
from rapidsms_httprouter.models import Message
from contact.forms import FreeSearchTextForm, DistictFilterMessageForm, ReplyTextForm, DistictFilterForm, MassTextForm
from contact.views import view_message_history
from django.contrib.auth.decorators import login_required
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^my-project/', include('my_project.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^admin/', include(admin.site.urls)),

    # RapidSMS core URLs
    (r'^account/', include('rapidsms.urls.login_logout')),
    url(r'^$', 'rapidsms.views.dashboard', name='rapidsms-dashboard'),
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
    url(r"^contact/(\d+)/message_history/$", view_message_history, name="message_history"),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        # helper URLs file that automatically serves the 'static' folder in
        # INSTALLED_APPS via the Django static media server (NOT for use in
        # production)
        (r'^', include('rapidsms.urls.static_media')),
    )

from rapidsms_httprouter.router import get_router
get_router(start_workers=True)


