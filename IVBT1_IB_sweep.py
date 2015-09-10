#import json
#import math
import os
#import random
#import sqlite3
#import time
#import traceback

import visa

from lib.sci9700 import Sci9700


## Configurations ---------------------------------------------------------------
debug_mode = False  # Set True while development without instruments.
sci_rsrc_name = 'GPIB0::1::INSTR'
sci_timeout_sec = 1

# Initialize -------------------------------------------------------------------
if debug_mode:
    sci_rsrc = None
else:
    rm = visa.ResourceManager()
    print(rm.list_resources())
    sci_rsrc = rm.open_resource(sci_rsrc_name)

sci = Sci9700(sci_rsrc, 1, debug_mode)


## Connect to database ----------------------------------------------------------
#if not os.path.exists(os.path.dirname(conf['02_sqlite3_file'])):
#    os.makedirs(os.path.dirname(conf['02_sqlite3_file']))
#sqlite3_connection = sqlite3.connect(conf['02_sqlite3_file'])
#cursor = sqlite3_connection.cursor()

## Create tables if not exist
#try:
#    cursor.execute('''
#        CREATE TABLE `parameters` (
#	        `t0`	INTEGER NOT NULL,
#	        `sample`	TEXT NOT NULL,
#	        `X`	INTEGER,
#	        `Y`	INTEGER,
#	        `xpos`	REAL,
#	        `ypos`	NUMERIC,
#	        `mesa`	TEXT,
#	        `status`	INTEGER,
#	        `measPoints`	INTEGER,
#	        `compliance`	REAL,
#	        `voltage`	REAL,
#	        `instrument`	TEXT,
#	        PRIMARY KEY(t0)
#        );''')
#except sqlite3.OperationalError:
#    print('Failed to create table "parameters" (maybe already exists)')
#try:
#    cursor.execute('''
#        CREATE TABLE `IV` (
#	        `id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
#	        `t0`	INTEGER NOT NULL,
#	        `V`	REAL,
#	        `I`	REAL
#        );''')
#except sqlite3.OperationalError:
#    print('Failed to create table "I-V" (maybe already exists)')
#try:
#    cursor.execute('''CREATE VIEW all_view AS
#        SELECT IV.*, parameters.* FROM parameters
#        INNER JOIN IV ON parameters.t0=IV.t0
#        ''')
#except sqlite3.OperationalError:
#    print('Failed to create view "all_view" (maybe already exists)')


## Measure ----------------------------------------------------------------------
#try:
#    first_measurement = True
#    # Get dimensions
#    suss.velocity = 25
#    suss.separate()
#    suss.velocity = 1
#    if not debug_mode:
#        input('Set substrate left bottom edge as home.')
#        suss.move_to_xy_from_home(-conf['dev_width'], -conf['dev_height'])
#        input('Right click substrate right top edge.')
#        (x_diagonal_from_home, y_diagonal_from_home, _) = suss.read_xyz('H')
#    else:
#        (x_diagonal_from_home, y_diagonal_from_home, _) = \
#            (-conf['dev_width'] - random.gauss(0, 50), -conf['dev_height'] - random.gauss(0, 50), 0)

#    # Calculate theta
#    theta_diagonal_tilled = math.atan(y_diagonal_from_home/x_diagonal_from_home) * 180/math.pi
#    theta_pattern_tilled = theta_diagonal_tilled - conf['dev_theta_diag']
#    print('theta_pattern_tilled:', theta_pattern_tilled)

#    # Measure I-Vs
#    for (X, Y) in conf['suss_XYs']:
#        if not first_measurement:
#            suss.align()  # Already separate if first
#        x_next_subs = conf['dev_x00'] + X * conf['dev_distance_between_mesa']
#        y_next_subs = conf['dev_y00'] + Y * conf['dev_distance_between_mesa']
#        (x_next_from_home, y_next_from_home) = rotate_vector(-x_next_subs, -y_next_subs, theta_pattern_tilled)
#        suss.move_to_xy_from_home(x_next_from_home, y_next_from_home)
#        suss.contact()
#        if first_measurement:
#            if not debug_mode:
#                input('Contact the prober.')
#            first_measurement = False
#        for V in conf['agi_Vs']:
#            t0 = int(time.strftime('%Y%m%d%H%M%S'))  # 20150830203015
#            Vs, Is, aborted = agi.double_sweep_from_zero(2, 1, V, None, conf['agi_comp'])
#            points = len(Vs)
#            cursor.execute('''INSERT INTO parameters VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
#                             (t0, conf['dev_sample'], X, Y, x_next_subs, y_next_subs,
#                              conf['dev_mesa'], 255, points, conf['agi_comp'], V,
#                              'SUSS PA300 + Agilent 4156C'))
#            tmp = zip([t0] * points, Vs, Is)  # [(t0, V0, I0), (t0, V1, I1), ...]
#            cursor.executemany('''INSERT INTO IV(t0, V, I) VALUES(?, ?, ?)''', tmp)  # IV.id: autofilled
#            sqlite3_connection.commit()
#            if debug_mode:
#                time.sleep(1)  # To avoid duplicates of "t0" in database
#            if aborted:
#                break

#except:
#    if not debug_mode:
#        with open(os.path.expanduser('~') + r'\Dropbox\work\0instr_report.txt', 'w') as f:
#            f.write(traceback.format_exc() + '\n')
#            del Vs, Is  # Because they are too long
#            f.write('\n---------- globals() ----------\n{}\n'.format(globals()))
#            f.write('\n---------- locals() ----------\n{}\n'.format(locals()))
#    raise

#else:
#    if not debug_mode:
#        with open(os.path.expanduser('~') + r'\Dropbox\work\0instr_report.txt', 'w') as f:
#            f.write('Measurement done.\n')
#            f.write('\n---------- locals() ----------\n{}\n'.format(locals()))
#            f.write('\n---------- globals() ----------\n{}\n'.format(globals()))

#finally:
#    # Close the database
#    cursor.close()

#print(0)
