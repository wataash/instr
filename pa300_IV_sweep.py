# Std libs
import json
import math
import os
import random
import sqlite3
import sys
import time
import traceback
# Non-std libs
import visa
# My libs
from lib.algorithms import rotate_vector
from lib.algorithms import zigzag_XY
from lib.agilent4156c import Agilent4156C
from lib.suss_pa300 import SussPA300


# Set True while development without instruments.
debug_mode = False
# If already calibrated theta
skip_calibrate_theta = True
if skip_calibrate_theta:
    theta_pattern_tilled = 0.9157978788395411


# Configurations ---------------------------------------------------------------
if sys.argv[0].endswith('.exe'):
    tmp = input('Learn usage from Ashihara before.')
    if tmp != 'do':
        raise RuntimeError()
    with open('pa300_IV_sweep.json') as f:
        j = json.load(f)
    j['sqlite3_file'] = 'IV.sqlite3'
    debug_mode = False
else:
    j = {}
    j['sqlite3_file'] = os.path.expanduser('~') + '/Documents/instr_data/IV.sqlite3'

    # Device data
    j['sample'] = 'E0325-2-1'
    j['mesa'] = ['D169', 'D56.3', 'D16.7', 'D5.54'][1]
    j['s_x00_offset'] = {'D169': 0, 'D56.3': +300, 'D16.7': +600, 'D5.54': +900}[j['mesa']]
    j['s_y00_offset'] = {'D169': 0, 'D56.3': 0, 'D16.7': 0, 'D5.54': 0}[j['mesa']]
    # s_: substrate
    # TODO: get from database
    j['s_distance_between_mesa'] = 1300
    j['s_height'] = 5582
    j['s_width'] = 13667
    j['s_max_X'] = 11
    j['s_max_Y'] = 4
    # Caluculated values by theta.py
    # TODO: get from database
    j['s_theta_diag'] = 21.3
    j['s_x00'] = -880 + j['s_x00_offset']
    j['s_y00'] = -866 + j['s_y00_offset']

    # VISA config
    j['visa_rsrc_name_agi'] = 'GPIB0::18::INSTR'
    j['visa_rsrc_name_suss'] = 'GPIB0::7::INSTR'
    j['visa_timeout_sec_agi'] = 600
    j['visa_timeout_sec_suss'] = 10

    # Measurement config
    j['agi_comp'] = 10e-3
    j['agi_Vs'] = [0.2, -0.2]
    j['XYs'] = zigzag_XY(1, 4, j['s_max_X'], j['s_max_Y'], False)

    with open('pa300_IV_sweep.json', 'w') as f:
        json.dump(j, f)

    if debug_mode:
        j['sample'] = 'debug sample'
        j['mesa'] = 'debug mesa'


# Connect to database ----------------------------------------------------------
sqlite3_connection = sqlite3.connect(j['sqlite3_file'])
cursor = sqlite3_connection.cursor()


# Initialize -------------------------------------------------------------------
if debug_mode:
    j['agi_rsrc'] = None
    suss_rsrc = None
else:
    rm = visa.ResourceManager()
    print(rm.list_resources())
    j['agi_rsrc'] = rm.open_resource(j['visa_rsrc_name_agi'])
    suss_rsrc = rm.open_resource(j['visa_rsrc_name_suss'])

agi = Agilent4156C(j['agi_rsrc'], j['visa_timeout_sec_agi'], False, debug_mode)
suss = SussPA300(suss_rsrc, j['visa_timeout_sec_suss'], debug_mode)


# Measure ----------------------------------------------------------------------
try:
    first_measurement = True

    if not skip_calibrate_theta:
        # Get dimensions
        suss.velocity = 25
        suss.separate()
        suss.velocity = 1
        if not debug_mode:
            input('Set substrate left bottom edge as home.')
            suss.move_to_xy_from_home(-j['s_width'], -j['s_height'])
            input('Right click substrate right top edge.')
            (x_diagonal_from_home, y_diagonal_from_home, _) = suss.read_xyz('H')
        else:
            (x_diagonal_from_home, y_diagonal_from_home, _) = \
                (-j['s_width'] - random.gauss(0, 50), -j['s_height'] - random.gauss(0, 50), 0)

        # Calibrate theta
        theta_diagonal_tilled = math.atan(y_diagonal_from_home/x_diagonal_from_home) * 180/math.pi
        theta_pattern_tilled = theta_diagonal_tilled - j['s_theta_diag']
        print('theta_pattern_tilled:', theta_pattern_tilled)
    else:
        suss.velocity = 1
        suss.separate()

    # Measure I-Vs
    for (X, Y) in j['XYs']:
        print('X{}Y{}'.format(X, Y))
        if not first_measurement:
            suss.align()  # Already separate if first
        x_next_subs = j['s_x00'] + X * j['s_distance_between_mesa']
        y_next_subs = j['s_y00'] + Y * j['s_distance_between_mesa']
        (x_next_from_home, y_next_from_home) = rotate_vector(-x_next_subs, -y_next_subs, theta_pattern_tilled)
        suss.move_to_xy_from_home(x_next_from_home, y_next_from_home)
        suss.contact()
        if first_measurement:
            if not debug_mode:
                input('Contact the prober.')
            first_measurement = False
        for V in j['agi_Vs']:
            t0 = int(time.strftime('%Y%m%d%H%M%S'))  # 20150830203015
            Vs, Is, aborted = agi.double_sweep_from_zero(2, 1, V, None, j['agi_comp'])
            points = len(Vs)
            # XY offset: UPDATE parameters SET X=X+8, Y=Y+12 WHERE sample="E0339 X9-12 Y13-16" and mesa="D56.3"
            cursor.execute('INSERT INTO parameters(t0,sample,X,Y,mesa,status,measPoints,compliance,voltage,instrument) \
                            VALUES(?,?,?,?,?,?,?,?,?,?)',
                            (t0, j['sample'], X, Y, j['mesa'],
                             255, points, j['agi_comp'], V, 'SUSS PA300 + Agilent 4156C'))
            tmp = zip([t0] * points, Vs, Is)  # [(t0, V0, I0), (t0, V1, I1), ...]
            cursor.executemany('''INSERT INTO IV(t0, V, I) VALUES(?, ?, ?)''', tmp)  # IV.id: autofilled
            sqlite3_connection.commit()
            if debug_mode:
                time.sleep(1)  # To avoid duplicates of "t0" in database
            if aborted:
                break
        # TODO: calculate R

except:
    if not debug_mode:
        with open(os.path.expanduser('~') + r'\Dropbox\work\0instr_report.txt', 'w') as f:
            f.write(traceback.format_exc() + '\n')
            del Vs, Is  # Because they are too long
            f.write('\n---------- globals() ----------\n{}\n'.format(globals()))
            f.write('\n---------- locals() ----------\n{}\n'.format(locals()))
    raise

else:
    if not debug_mode:
        with open(os.path.expanduser('~') + r'\Dropbox\work\0instr_report.txt', 'w') as f:
            f.write('Measurement done.\n')
            f.write('\n---------- locals() ----------\n{}\n'.format(locals()))
            f.write('\n---------- globals() ----------\n{}\n'.format(globals()))

finally:
    # Close the database
    cursor.close()

input('Done.')
