from django.shortcuts import redirect, get_object_or_404, render_to_response
from rapidsms.models import Contact
from django.template import RequestContext
# from .utils import reminders

def delete_reminder(req):
  raise Exception, 'Ras-le-bol.'

def view_mother(req, mother_id):
    mother = get_object_or_404(Contact, pk=mother_id)
    return render_to_response(
    "mr/mother.html",
    { 'mother': mother, 'reminders': reminders(mother.last_menses) },
    context_instance=RequestContext(req))
