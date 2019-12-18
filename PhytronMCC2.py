#!/usr/bin/python -u
from PyTango.server import run
from PyTango import Database
import os
from PhytronMCC2Axis import PhytronMCC2Axis
from PhytronMCC2Ctrl import PhytronMCC2Ctrl

TANGO_HOST = os.environ['TANGO_HOST']
print('Check TANGO_HOST: {:s}'.format(TANGO_HOST))

db = Database()
if db.check_tango_host(TANGO_HOST) is None:
    print('TANGO_HOST format is okay')
else:
    print('TANGO_HOST format is bad')

print('Check connection to TANGO database')
try:
    print(db.get_info())
except Exception:
    print('Could not connect to TANGO database')
    exit(255)

print('Run PhytronMCC2Ctrl & PhytronMCC2Axis')
run((PhytronMCC2Ctrl, PhytronMCC2Axis,))
