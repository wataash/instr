import json
import math
import os
import random
import time
import traceback

import visa

import algorithms
import configure
from agilent4156c import Agilent4156C
from suss_pa300 import SussPA300


# Configurations ---------------------------------------------------------------
# If develop on desktop (without instruments), make this true.
debug_mode = True

if debug_mode:
    try:
        with open(os.environ['appdata'] + r'\instr\Agilent4156C.json') as f:
            conf = json.load(f)
    except FileNotFoundError:
        with open('dummy_data/Agilent4156C.json') as f:
            conf = json.load(f)
else:
    raise NotImplementedError  # TODO
    # config = configure.main()


# Initialize -------------------------------------------------------------------
if debug_mode:
    a = Agilent4156C(None, conf['agilent_visa_timeout_sec'], False, True)
    s = SussPA300(None, conf['suss_visa_timeout_sec'], True)
else:
    rm = visa.ResourceManager()
    print(rm.list_resources())
    a = Agilent4156C(
        rm.open_resource(conf['agilent_visa_resource_name']), conf['agilent_visa_timeout_sec'], False, False)
    s = SussPA300(rm.open_resource(
        conf['suss_visa_resource_name']), conf['suss_visa_timeout_sec'], False, False)


# Measure ----------------------------------------------------------------------
first_measurement = True
try:
    # Get dimensions
    s.velocity = 25
    s.moveZ(conf['z_separate'] - 100)
    s.velocity = 1
    if not debug_mode:
        input('Set substrate left bottom edge as home.')
        s.move_to_xy_from_home(-conf['subs_width'], -conf['subs_height'])
        input('Right click substrate right top edge.')
        (x_diagonal_from_home, y_diagonal_from_home, _) = s.read_xyz('H')
    else:
        (x_diagonal_from_home, y_diagonal_from_home, _) = \
            (-conf['subs_width'] - random.gauss(0, 50), -conf['subs_height'] - random.gauss(0, 50), 0)

    # Calculate theta
    theta_diagonal_tilled = math.atan(y_diagonal_from_home/x_diagonal_from_home) * 180/math.pi
    theta_pattern_tilled = theta_diagonal_tilled - conf['theta_diagonal']
    print(theta_pattern_tilled)

    # Measure I-Vs
    for (X, Y) in conf['meas_XYs']:
        s.moveZ(conf['z_separate'])  # s.align()
        x_next_subs = conf['x00_subs'] + X * conf['distance_between_mesa']
        y_next_subs = conf['y00_subs'] + Y * conf['distance_between_mesa']
        (x_next_from_home, y_next_from_home) = algorithms.rotate_vector(-x_next_subs, -y_next_subs, theta_pattern_tilled)
        s.move_to_xy_from_home(x_next_from_home, y_next_from_home)
        s.moveZ(conf['z_contact'])  # s.contact()
        if first_measurement:
            if debug_mode:
                pass
            else:
                input('Contact the prober.')
            first_measurement = False
        for V in conf['meas_Vs']:
            t0 = time.strftime('%Y%m%d-%H%M%S')
            Vs, Is, aborted = a.double_sweep_from_zero(2, 1, V, V/1000, 10e-6, 10e-3)
            filename = 'double-sweep_{}_{}_X{}_Y{}_{}_{}V.csv'.format(t0, conf['sample'], X, Y, conf['mesa'], V)
            points = len(Vs)
            with open(conf['datadir'] + '\\' + filename, 'w') as f:
                Vs = [str(elem) for elem in Vs]
                Vs = ','.join(Vs)
                f.write(Vs)  # V, V, V, ... TODO: transpose
                f.write('\n')
                Is = [str(elem) for elem in Is]
                Is = ','.join(Is)
                f.write(Is)  # I, I, I, ... TODO: transpose
                f.write('\n')
            with open(conf['datadir'] + '\\double-sweep_params.csv', 'a') as f:
                f.write('t0={},sample=E0326-2-1,X={},Y={},xpos={},ypos={},mesa={},status=255,measPoints={},comp=0.01,instr=SUSS PA300, originalFileName={}\n'.
                       format(t0, X, Y, x_next_subs, y_next_subs, conf['mesa'], points, filename))
                # t0=20150717-125846, sample=E0326-2-1,X=5,Y=3,xpos=5921.5,ypos=3031.5,mesa=D56.3,status=255,measPoints=101,comp=0.01,instr=SUSS PA300, originalFileName=double-sweep_20150717-125846_E0326-2-1_X5_Y3_D56.3_0.1V.csv
            if aborted:
                break
except:
    if debug_mode:
        raise
    with open(os.path.expanduser('~') + r'\Dropbox\work\0instr_report.txt', 'w') as f:
        f.write(traceback.format_exc() + '\n')
        del Vs, Is  # Because they are too long
        f.write('\n---------- globals() ----------\n{}\n'.format(globals()))
        f.write('\n---------- locals() ----------\n{}\n'.format(locals()))
    raise
else:
    with open(os.path.expanduser('~') + r'\Dropbox\work\instr_report.txt', 'w') as f:
        f.write('Measurement done.\n')
        f.write('\n---------- locals() ----------\n{}\n'.format(locals()))
        f.write('\n---------- globals() ----------\n{}\n'.format(globals()))

print(0)
