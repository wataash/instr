# Built-in libs
import math
import os
import random
import sqlite3
import time
import traceback
# Installed libs
import visa
# My libs
from lib.algorithms import rotate_vector
from lib.algorithms import zigzag_XY
from lib.agilent4156c import Agilent4156C
from lib.suss_pa300 import SussPA300


# Set True while development without instruments.
debug_mode = True


# Configurations ---------------------------------------------------------------
sqlite3_file = os.path.expanduser('~') + '/Documents/instr_data/IV.sqlite3'

# Device data
sample = "E0326-2-1"
mesa = ['D169', 'D56.3', 'D16.7', 'D5.54'][1]
# s_: substrate
s_distance_between_mesa = 1300
s_height = 25000.0
s_width = 24700.0
s_max_X = 17
s_max_Y = 17
# Caluculated values by theta.py
s_theta_diag = 46.7
s_x00 = 905.0
s_y00 = 1200.0

# VISA config
visa_rsrc_name_agi = "GPIB0::18::INSTR"
visa_rsrc_name_suss = "GPIB0::7::INSTR"
visa_timeout_sec_agi = 600
visa_timeout_sec_suss = 10

# Measurement config
agi_comp = 10e-3
agi_Vs = [ 0.1, -0.1 ]
XYs = zigzag_XY(1, 1, 2, 2)

if debug_mode:
    sample = 'debug sample'
    mesa = 'debug mesa'


# Connect to database ----------------------------------------------------------
sqlite3_connection = sqlite3.connect(sqlite3_file)
cursor = sqlite3_connection.cursor()


# Initialize -------------------------------------------------------------------
if debug_mode:
    agi_rsrc = None
    suss_rsrc = None
else:
    rm = visa.ResourceManager()
    print(rm.list_resources())
    agi_rsrc = rm.open_resource(visa_rsrc_name_agi)
    suss_rsrc = rm.open_resource(visa_rsrc_name_suss)

agi = Agilent4156C(agi_rsrc, visa_timeout_sec_agi, False, debug_mode)
suss = SussPA300(suss_rsrc, visa_timeout_sec_suss, debug_mode)


# Measure ----------------------------------------------------------------------
try:
    first_measurement = True
    # Get dimensions
    suss.velocity = 25
    suss.separate()
    suss.velocity = 1
    if not debug_mode:
        input('Set substrate left bottom edge as home.')
        suss.move_to_xy_from_home(-s_width, -s_height)
        input('Right click substrate right top edge.')
        (x_diagonal_from_home, y_diagonal_from_home, _) = suss.read_xyz('H')
    else:
        (x_diagonal_from_home, y_diagonal_from_home, _) = \
            (-s_width - random.gauss(0, 50), -s_height - random.gauss(0, 50), 0)

    # Calculate theta
    theta_diagonal_tilled = math.atan(y_diagonal_from_home/x_diagonal_from_home) * 180/math.pi
    theta_pattern_tilled = theta_diagonal_tilled - s_theta_diag
    print('theta_pattern_tilled:', theta_pattern_tilled)

    # Measure I-Vs
    for (X, Y) in XYs:
        print('X{}Y{}'.format(X, Y))
        if not first_measurement:
            suss.align()  # Already separate if first
        x_next_subs = s_x00 + X * s_distance_between_mesa
        y_next_subs = s_y00 + Y * s_distance_between_mesa
        (x_next_from_home, y_next_from_home) = rotate_vector(-x_next_subs, -y_next_subs, theta_pattern_tilled)
        suss.move_to_xy_from_home(x_next_from_home, y_next_from_home)
        suss.contact()
        if first_measurement:
            if not debug_mode:
                input('Contact the prober.')
            first_measurement = False
        for V in agi_Vs:
            t0 = int(time.strftime('%Y%m%d%H%M%S'))  # 20150830203015
            Vs, Is, aborted = agi.double_sweep_from_zero(2, 1, V, None, agi_comp)
            points = len(Vs)
            cursor.execute('''INSERT INTO parameters VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
                             (t0, sample, X, Y, x_next_subs, y_next_subs,
                              mesa, 255, points, agi_comp, V,
                              'SUSS PA300 + Agilent 4156C'))
            tmp = zip([t0] * points, Vs, Is)  # [(t0, V0, I0), (t0, V1, I1), ...]
            cursor.executemany('''INSERT INTO IV(t0, V, I) VALUES(?, ?, ?)''', tmp)  # IV.id: autofilled
            sqlite3_connection.commit()
            if debug_mode:
                time.sleep(1)  # To avoid duplicates of "t0" in database
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
    # Close the database
    cursor.close()

print(0)
