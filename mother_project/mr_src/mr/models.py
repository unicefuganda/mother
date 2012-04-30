from script.signals import script_progress_was_completed, script_progress
from django.db.models.signals import post_syncdb
from django.db import *
from .utils import mr_autoreg, init_structures, validate_district
import datetime
import re
import sys
from poll.models import Poll
from django.core.exceptions import ValidationError
from eav.models import Attribute
from healthmodels.models import HealthProvider
from django.db import models

post_syncdb.connect(init_structures, weak=False)
script_progress_was_completed.connect(mr_autoreg, weak=False)
script_progress.connect(validate_district, weak = False)

class ReminderMessage(models.Model):
  week_number   = models.IntegerField()
  day_number    = models.IntegerField()
  reminder_text = models.TextField()

  def __unicode__(self):
    return u'Week %d, Day %d: "%s"' % (self.week_number, self.day_number, self.reminder_text)

  @classmethod
  def as_hash(self):
    ans = {}
    for rm in self.objects.all():
      week  = ans.get(rm.week_number)
      if not week:
        week  = {}
        ans[rm.week_number] = week
      week[rm.day_number] = rm.reminder_text
    return ans

class Questionnaire(models.Model):
    health_worker       = models.ForeignKey(HealthProvider)
    first_anc_visit     = models.IntegerField()
    fourth_anc_visit    = models.IntegerField()
    art_treated_mums    = models.IntegerField()
    six_month_hiv_diag  = models.IntegerField()

    def __unicode__(self):
        return '%s: %d, %d, %d, %d' % (str(health_worker), first_anc_visit, fourth_anc_visit, art_treated_mums, six_month_hiv_diag)

def dl_distance(s1, s2):
    """
    Computes the Damerau-Levenshtein distance between two strings.  Not the fastest implementation
    in the world, but works for our purposes.

    Ripped from: http://www.guyrutenberg.com/2008/12/15/damerau-levenshtein-distance-in-python/
    """
    d = {}
    lenstr1 = len(s1)
    lenstr2 = len(s2)
    for i in xrange(-1, lenstr1 + 1):
        d[(i, -1)] = i + 1
    for j in xrange(-1, lenstr2 + 1):
        d[(-1, j)] = j + 1

    for i in xrange(0, lenstr1):
        for j in xrange(0, lenstr2):
            if s1[i] == s2[j]:
                cost = 0
            else:
                cost = 1
            d[(i, j)] = min(
                           d[(i - 1, j)] + 1, # deletion
                           d[(i, j - 1)] + 1, # insertion
                           d[(i - 1, j - 1)] + cost, # substitution
                          )
            if i > 1 and j > 1 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min (d[(i, j)], d[i - 2, j - 2] + cost) # transposition

    return d[lenstr1 - 1, lenstr2 - 1]


def parse_timedelta(value):
    lvalue = value.lower().strip()
    now = datetime.datetime.now()
    try:
        return (now - datetime.datetime.strptime(lvalue, '%m-%d-%Y')).days
    except ValueError:
        try:
            return (now - datetime.datetime.strptime(lvalue, '%m/%d/%Y')).days
        except ValueError:
            rx = re.compile('[0-9]*')
            m = rx.match(lvalue)
            number = lvalue[m.start():m.end()].strip()
            unit = lvalue[m.end():].strip()
            if number:
                number = int(number)
                unit_amounts = {
                    'd':1,
                    'w':7,
                    'm':30,
                    'y':365,
                }
                unit_dict = {
                    'd':('day', 'days', 'dys', 'ds'),
                    'w':('wk', 'wks', 'weeks', 'week'),
                    'm':('mo', 'months', 'month', 'mnths', 'mos', 'ms', 'mns', 'mnth'),
                    'y':('year', 'years', 'yr', 'yrs'),
                }
                for key, words in unit_dict.iteritems():
                    if unit == key:
                        return number * unit_amounts[key]
                    for word in words:
                        if dl_distance(word, unit) <= 1:
                            return number * unit_amounts[key]
        # raise ValidationError

Poll.register_poll_type('timedelt', 'Time Length', parse_timedelta, db_type=Attribute.TYPE_FLOAT)
