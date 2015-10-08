# Std libs
import json
import math
import os
import random
import shutil
import sqlite3
import time
import traceback
# Non-std libs
#import visa
# My libs
import constants as c
from lib.algorithms import rotate_vector
from lib.algorithms import zigzag_XY
from lib.agilent4156c import Agilent4156C
from lib.suss_pa300 import SussPA300


# Set True while development without instruments.
debug_mode = False

# If already calibrated theta
skip_calibrate_theta = False
if skip_calibrate_theta:
    # TODO: query meas IV now?
    theta_pattern_tilled = -0.0933619805775443
    input('Use theta_pattern_tilled: {}'.format(theta_pattern_tilled))

if debug_mode:
    c.sw_sample = 'debug_sample'
    c.sw_mesas = c.sw_mesas_debug
    c.sql_params = c.sql_params_debug
    c.sw_sql_IVs = c.sql_IVs_debug
else:
    import visa

# Connect to database
conn_params = sqlite3.connect(c.sql_params)
cur_params = conn_params.cursor()
conn_IVs = sqlite3.connect(c.sw_sql_IVs)
cur_IVs = conn_IVs.cursor()

s_width, s_height, s_theta_diag, s_x00, s_y00, s_d_X, s_d_Y, X_min, X_max, Y_min, Y_max = \
    cur_params.execute('SELECT width, height, theta_diag, x00, y00, d_X, d_Y, \
                    X_min, X_max, Y_min, Y_max \
                    FROM samples WHERE sample=?',
                    (c.sw_sample,)).fetchone()

XYs = zigzag_XY(X_min, Y_min, X_max, Y_max, 'r') # TODO: exception for first


# Initialize -------------------------------------------------------------------
if debug_mode:
    agi_rsrc = None
    suss_rsrc = None
else:
    rm = visa.ResourceManager()
    print(rm.list_resources())
    agi_rsrc = rm.open_resource(c.visa_rsrc_name_agi)
    suss_rsrc = rm.open_resource(c.visa_rsrc_name_suss)

agi = Agilent4156C(agi_rsrc, c.visa_timeout_sec_agi, False, debug_mode)
suss = SussPA300(suss_rsrc, c.visa_timeout_sec_suss, debug_mode)


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
            suss.move_to_xy_from_home(-s_width, -s_height)
            input('Right click substrate right top edge.')
            (x_diagonal_from_home, y_diagonal_from_home, _) = suss.read_xyz('H')
        else:
            (x_diagonal_from_home, y_diagonal_from_home, _) = \
                (-s_width - random.gauss(0, 50), -s_height - random.gauss(0, 50), 0)

        # Calibrate theta
        theta_diagonal_tilled = math.atan(y_diagonal_from_home/x_diagonal_from_home) * 180/math.pi
        theta_pattern_tilled = theta_diagonal_tilled - s_theta_diag
        print('theta_pattern_tilled:', theta_pattern_tilled)
    else:
        suss.velocity = 1
        suss.separate()

    # Measure I-Vs.  Be sure separate!
    for mesa in c.sw_mesas:
        print('mesa:', mesa)
        m_mask, m_name, m_area, m_circumference, \
            m_x_offset_center, m_y_offset_center, m_x_offset_probe, m_y_offset_probe = \
            cur_params.execute('SELECT mask, name, area, circumference, \
                                x_offset_center, y_offset_center, x_offset_probe, y_offset_probe \
                                FROM mesas WHERE name=?',
                                (mesa,)).fetchone()
        # TODO: offset exceptions
        print(m_x_offset_probe, m_y_offset_probe)
        m_x_offset_probe, m_y_offset_probe = 0, 0 # 80, -80
        for (X, Y) in XYs:
            print('X{}Y{}'.format(X, Y))
            #if not first_measurement:
            #    suss.align()  # Already separate if first
            x_next_subs = s_x00 + m_x_offset_center + m_x_offset_probe + X * s_d_X
            y_next_subs = s_y00 + m_y_offset_center + m_y_offset_probe + Y * s_d_Y
            (x_next_from_home, y_next_from_home) = rotate_vector(-x_next_subs, -y_next_subs, theta_pattern_tilled)
            suss.move_to_xy_from_home(x_next_from_home, y_next_from_home)
        #    suss.contact()
        #    if first_measurement and mesa == c.sw_mesas[0]:
        #        # TODO: move upper
        #        if not debug_mode:
        #            input('Contact the prober.')
        #        first_measurement = False
        #    for V in c.sw_agi_Vs:
        #        t0 = int(time.strftime('%Y%m%d%H%M%S'))  # 20150830203015
        #        Vs, Is, aborted = agi.double_sweep_from_zero(2, 1, V, None, c.sw_agi_comp)
        #        points = len(Vs)
        #        # XY offset: UPDATE params SET X=X+8, Y=Y+12 WHERE sample="E0339 X9-12 Y13-16" and mesa="D56.3"
        #        cur_params.execute('INSERT INTO IV_params(t0,sample,X,Y,mesa,status,measPoints,compliance,voltage,instrument) \
        #                        VALUES(?,?,?,?,?,?,?,?,?,?)',
        #                        (t0, c.sw_sample, X, Y, mesa,
        #                         255, points, c.sw_agi_comp, V, 'SUSS PA300 + Agilent 4156C'))
        #        tmp = zip([t0] * points, Vs, Is)  # [(t0, V0, I0), (t0, V1, I1), ...]
        #        cur_IVs.executemany('''INSERT INTO IVs(t0, V, I) VALUES(?, ?, ?)''', tmp)
        #        conn_params.commit()
        #        conn_IVs.commit()
        #        if debug_mode:
        #            time.sleep(1)  # To avoid duplicates of "t0" in database
        #        if aborted:
        #            break
        #    suss.align()
        #    # TODO: calculate R
        #suss.separate()

except:
    if not debug_mode:
        with open(os.path.expanduser('~') + r'\Dropbox\work\0instr_report.txt', 'w') as f:
            f.write(traceback.format_exc() + '\n')
            # TODO f.write mesa, X, Y
            #del Vs, Is  # Because they are too long  # error if the doesn't exist
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
    cur_params.close()
    cur_IVs.close()
    #shutil.copy2(db_params, db_copy_dir)  # TODO: test, mkdir if not exist
    #shutil.copy2(db_IVs, db_copy_dir)

input('Done.')
