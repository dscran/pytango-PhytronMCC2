# PhytronMcc2Run.py

from PyTango.server import run
from PhytronMCC2Axis import PhytronMCC2Axis
from PhytronMCC2Ctrl import PhytronMCC2Ctrl

run([PhytronMCC2Ctrl, PhytronMCC2Axis])
