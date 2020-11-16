#!/usr/bin/python3 -u
from tango.server import run
import os
from PhytronMCC2Axis import PhytronMCC2Axis
from PhytronMCC2Ctrl import PhytronMCC2Ctrl

print('Run PhytronMCC2Ctrl & PhytronMCC2Axis')
run([PhytronMCC2Ctrl, PhytronMCC2Axis])
