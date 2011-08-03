#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import sys, os
from django.core.management import execute_manager
import settings

filedir = os.path.dirname(__file__)
sys.path.append(os.path.join(filedir))
sys.path.append(os.path.join(filedir, 'rapidsms', 'lib'))
sys.path.append(os.path.join(filedir, 'rapidsms-contact'))
sys.path.append(os.path.join(filedir, 'rapidsms-generic'))
sys.path.append(os.path.join(filedir, 'rapidsms-httprouter'))
sys.path.append(os.path.join(filedir, 'rapidsms-polls'))
sys.path.append(os.path.join(filedir, 'rapidsms-script'))
sys.path.append(os.path.join(filedir, 'rapidsms-ureport'))
sys.path.append(os.path.join(filedir, 'healthmodels'))
sys.path.append(os.path.join(filedir, 'eav'))

if __name__ == "__main__":
    execute_manager(settings)
