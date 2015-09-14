"""
Builds a stand-alone .exe file.
"""

import sys
from distutils.core import setup
import py2exe

sys.argv.append('py2exe')
setup(console=['pa300_theta.py', 'pa300_IV_sweep.py'])
#setup(console=['pa300_IV_sweep.py'])
