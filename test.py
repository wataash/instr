import math
import os
import time
import traceback

import visa

from agilent4156c import Agilent4156C
from suss_pa300 import SussPA300

# User inputs ------------------------------------------------------------------
# VISA configurations
agilent_visa_resource_name = 'GPIB0::18::INSTR'  # 'GPIB1::18::INSTR'
agilent_visa_timeout_sec = 600  # 10min
suss_visa_resource_name = 'GPIB0::7::INSTR'  # 'GPIB1::7::INSTR'
suss_visa_timeout_sec = 10
# Directory
datadir = os.environ['appdata'] + r'\Instr\Agilent4156C'
# Device information
mesa = 'D56.3'
distance_between_mesa = 1300
last_X = 11
last_Y = 4
subs_width = 13500  # approximately
subs_height = 4500  # approx
# Use theta.py
# (theta_diagonal, x00_subs, y00_subs) = (21.44501633542317, -890.5720364478045, -878.5148369616054)  # D169
(theta_diagonal, x00_subs, y00_subs) = (21.44501633542317, -890.5720364478045 + 300, -878.5148369616054)  # D56.3
# (theta_diagonal, x00_subs, y00_subs) = (21.44501633542317, -890.5720364478045 + 600, -878.5148369616054)  # D16.7
# (theta_diagonal, x00_subs, y00_subs) = (21.44501633542317, -890.5720364478045 + 900, -878.5148369616054)  # D5.??
# Measurement configurations
z_contact = 12000
z_separate = z_contact - 100
# meas_XYs = [(1, 1), (3, 2), (1, 2), (2, 1)]
meas_XYs = [(X, 1) for X in range(1, 11)] + [(X, 2) for X in reversed(range(3, 12))] + \
           [(X, 3) for X in range(3, 12)] + [(X, 4) for X in reversed(range(2, 11))]
# meas_Vs = [0.1, -0.1, 0.2, -0.2, 0.3, -0.3, -0.4, 0.4, -0.5, 0.5]
meas_Vs = [0.1, -0.1, 0.2, -0.2, 0.3, -0.3]

# Initialize -------------------------------------------------------------------
rm = visa.ResourceManager()
print(rm.list_resources())
a = Agilent4156C(rm.open_resource(agilent_visa_resource_name), agilent_visa_timeout_sec, False, False)
s = SussPA300(rm.open_resource(suss_visa_resource_name), suss_visa_timeout_sec, False)

def rotate_vector(x, y, theta_deg):
    theta_rad = theta_deg * math.pi/180
    return math.cos(theta_rad)*x - math.sin(theta_rad)*y, math.sin(theta_rad)*x + math.cos(theta_rad)*y

# Measure ----------------------------------------------------------------------
try:
    s.velocity = 15
    s.moveZ(z_separate - 100)
    s.velocity = 1
    input('Set substrate left bottom edge as home.')
    s.move_to_xy_from_home(-subs_width, -subs_height)
    input('Right click substrate right top edge.')
    (x_diagonal_from_home, y_diagonal_from_home, _) = s.read_xyz('H')  # -13803.0, -5211.0, 11800.0
    theta_diagonal_tilled = math.atan(y_diagonal_from_home/x_diagonal_from_home) * 180/math.pi  # 20.6829
    theta_pattern_tilled = theta_diagonal_tilled - theta_diagonal  # -0.76216
    for (X, Y) in meas_XYs:
        s.moveZ(z_separate)  # s.align()
        x_next_subs = x00_subs + X * distance_between_mesa
        y_next_subs = y00_subs + Y * distance_between_mesa
        (x_next_from_home, y_next_from_home) = rotate_vector(-x_next_subs, -y_next_subs, theta_pattern_tilled)
        s.move_to_xy_from_home(x_next_from_home, y_next_from_home)
        s.moveZ(z_contact)  # s.contact()
        for V in meas_Vs:
            t0 = time.strftime('%Y%m%d-%H%M%S')
            Vs, Is, aborted = a.double_sweep_from_zero(2, 1, V, V/1000, 10e-6, 10e-3)
            filename = 'double-sweep_{}_E0326-2-1_X{}_Y{}_{}_{}V.csv'.format(t0, X, Y, mesa, V)
            points = len(Vs)
            with open(datadir + '\\' + filename, 'w') as f:
                Vs = [str(elem) for elem in Vs]
                Vs = ','.join(Vs)
                f.write(Vs)  # V, V, V, ...
                f.write('\n')
                Is = [str(elem) for elem in Is]
                Is = ','.join(Is)
                f.write(Is)  # I, I, I, ...
                f.write('\n')
            with open(datadir + '\\double-sweep_params.csv', 'a') as f:
                f.write('t0={},sample=E0326-2-1,X={},Y={},xpos={},ypos={},mesa={},status=255,measPoints={},comp=0.01,instr=SUSS PA200, originalFileName={}\n'.
                       format(t0, X, Y, x_next_subs, y_next_subs, mesa, points, filename))
                # t0=20150717-125846, sample=E0326-2-1,X=5,Y=3,xpos=5921.5,ypos=3031.5,mesa=D56.3,status=255,measPoints=101,comp=0.01,instr=SUSS PA200, originalFileName=double-sweep_20150717-125846_E0326-2-1_X5_Y3_D56.3_0.1V.csv
            if aborted:
                break
except:
    with open(os.path.expanduser('~') + r'\Dropbox\work\0instr_report.txt', 'w') as f:
        f.write(traceback.format_exc() + '\n')
        # del Vs, Is  # Because they are too long
        f.write('\n---------- globals() ----------\n{}\n'.format(globals()))
        f.write('\n---------- locals() ----------\n{}\n'.format(locals()))
    raise
else:
    with open(os.path.expanduser('~') + r'\Dropbox\work\instr_report.txt', 'w') as f:
        f.write('Measurement done.\n')
        f.write('\n---------- locals() ----------\n{}\n'.format(locals()))
        f.write('\n---------- globals() ----------\n{}\n'.format(globals()))

print(0)
