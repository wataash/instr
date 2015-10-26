"""
Builds a stand-alone .exe file.
"""

# Std libs
import sys
from distutils.core import setup
# Non-std libs
import py2exe

sys.argv.append('py2exe')
setup(console=['pa300_theta.py', 'pa300_IV_sweep.py'])
#setup(console=['pa300_IV_sweep.py'])
