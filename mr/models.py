from script.signals import script_progress_was_completed, script_progress
from django.db.models.signals import post_syncdb
from .utils import mr_autoreg, init_structures

post_syncdb.connect(init_structures, weak=False)
script_progress_was_completed.connect(mr_autoreg, weak=False)
