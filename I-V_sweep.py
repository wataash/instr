import json
import math
import os
import random
import sqlite3
import time
import traceback

import visa

from lib.algorithms import rotate_vector
from lib.agilent4156c import Agilent4156C
from lib.suss_pa300 import SussPA300
import configure


# Set True while desktop development (without instruments).
debug_mode = True


# Configurations ---------------------------------------------------------------

conf = configure.main()
if debug_mode:
    conf['sample'] = 'debug sample'
    conf['meas_XYs'] = [(1, 1), (2, 3)]


# Initialize -------------------------------------------------------------------
if debug_mode:
    agi_rsrc = None
    suss_rsrc = None
else:
    rm = visa.ResourceManager()
    print(rm.list_resources())
    agi_rsrc = rm.open_resource(conf['agilent_visa_rsrc_name'])
    suss_rsrc = rm.open_resource(conf['suss_visa_rsrc_name'])

agi = Agilent4156C(agi_rsrc, conf['agi_visa_timeout_sec'], False, debug_mode)
suss = SussPA300(suss_rsrc, conf['suss_visa_timeout_sec'], debug_mode)


# Connect to database ----------------------------------------------------------
conn = sqlite3.connect(conf['data_dir'] + '/database.sqlite3')
c = conn.cursor()

# Create tables if not exist
try:
    c.execute('''CREATE TABLE `parameters` (
        `t0`	TEXT NOT NULL,
        `sample`	TEXT NOT NULL,
        `X`	INTEGER,
        `Y`	INTEGER,
        `xpos`	REAL,
        `ypos`	REAL,
        `mesa`	TEXT,
        `status`	INTEGER,
        `measPoints`	INTEGER,
        `compliance`	REAL,
        `voltage`	REAL,
        `lib`	TEXT,
        PRIMARY KEY(t0)
    );''')
except sqlite3.OperationalError:
    print('table parameters already exists')
try:
    c.execute('''CREATE TABLE `parameters` (
            `id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            `t0`	TEXT NOT NULL,
            `sample`	REAL NOT NULL,
            `X`	INTEGER,
            `Y`	INTEGER,
            `xpos`	REAL,
            `ypos`	REAL,
            `mesa`	TEXT,
            `status`	INTEGER,
            `measPoints`	INTEGER,
            `compliance`	REAL,
            `voltage`	REAL,
            `instrument`	TEXT
        );;''')
except sqlite3.OperationalError:
    print('table I-V already exists')


# Measure ----------------------------------------------------------------------
try:
    first_measurement = True
    # Get dimensions
    suss.velocity = 25
    suss.moveZ(conf['z_separate'] - 100)
    suss.velocity = 1
    if not debug_mode:
        input('Set substrate left bottom edge as home.')
        suss.move_to_xy_from_home(-conf['subs_width'], -conf['subs_height'])
        input('Right click substrate right top edge.')
        (x_diagonal_from_home, y_diagonal_from_home, _) = suss.read_xyz('H')
    else:
        (x_diagonal_from_home, y_diagonal_from_home, _) = \
            (-conf['subs_width'] - random.gauss(0, 50), -conf['subs_height'] - random.gauss(0, 50), 0)

    # Calculate theta
    theta_diagonal_tilled = math.atan(y_diagonal_from_home/x_diagonal_from_home) * 180/math.pi
    theta_pattern_tilled = theta_diagonal_tilled - conf['theta_diagonal']
    print('theta_pattern_tilled:', theta_pattern_tilled)

    # Measure I-Vs
    for (X, Y) in conf['meas_XYs']:
        suss.moveZ(conf['z_separate'])  # s.align()
        x_next_subs = conf['x00_subs'] + X * conf['distance_between_mesa']
        y_next_subs = conf['y00_subs'] + Y * conf['distance_between_mesa']
        (x_next_from_home, y_next_from_home) = rotate_vector(-x_next_subs, -y_next_subs, theta_pattern_tilled)
        suss.move_to_xy_from_home(x_next_from_home, y_next_from_home)
        suss.moveZ(conf['z_contact'])  # s.contact()
        if first_measurement:
            if not debug_mode:
                input('Contact the prober.')
            first_measurement = False
        for V in conf['meas_Vs']:
            t0 = time.strftime('%Y-%m-%d %H:%M:%S')
            Vs, Is, aborted = agi.double_sweep_from_zero(2, 1, V, V/1000, 10e-6, conf['compliance'])
            # filename = 'double-sweep_{}_{}_X{}_Y{}_{}_{}V.csv'.format(t0, conf['sample'], X, Y, conf['mesa'], V)
            points = len(Vs)
            c.execute('''INSERT INTO parameters(t0, sample, X, Y, xpos, ypos, mesa, status, measPoints, compliance, voltage, instrument)
                             values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (t0, conf['sample'], X, Y, x_next_subs, y_next_subs,
                      conf['mesa'], 255, points, conf['compliance'], V,
                      'SUSS PA300 + Agilent 4156C'))
            tmp = zip([t0] * points, Vs, Is)  # [(t0, V0, I0), (t0, V1, I1), ...]
            c.executemany('''INSERT INTO IV(t0, V, I) values(?, ?, ?)''', tmp)

            if aborted:
                break

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
    # Commit and close database
    conn.commit()
    c.close()

print(0)
