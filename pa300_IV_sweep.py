debug_mode = False  # Set True while development without instruments.

# Std libs
from collections import defaultdict
import math
import os
import random
import shutil
import sqlite3
import time
import traceback
# Non-std libs
if not debug_mode:
    import visa
# My libs
import constants as c
from lib.algorithms import rotate_vector
from lib.algorithms import zigzag_XY
from lib.agilent4156c import Agilent4156C
from lib.suss_pa300 import SussPA300


sample = 'test sample'
if debug_mode:
    sample = 'debug_sample'
sql_IVs_local = c.local_dir + 'IVs_' + sample + '.sqlite3'

# Connect to database
if debug_mode:
    conn_params = sqlite3.connect(c.sql_params_local_debug)
    conn_IVs = sqlite3.connect(c.sql_IVs_local_debug)
else:
    conn_params = sqlite3.connect(c.sql_params_dropbox)
    conn_IVs = sqlite3.connect(sql_IVs_local)
cur_params = conn_params.cursor()
cur_IVs = conn_IVs.cursor()

mask, X_min, X_max, Y_min, Y_max = \
    cur_params.execute('SELECT mask, X_min, X_max, Y_min, Y_max \
                        FROM samples WHERE sample=?',
                       (sample,)).fetchone()

# parameters
if debug_mode:
    mesas = ['debug_mesa']
else:
    mesas = c.mesas[mask][2:16]

# default XYs
dicXYs = defaultdict(lambda: zigzag_XY(X_min, Y_min, X_max, Y_max, 'r'))
# exception XYs
#dicXYs['mesa#3'] = zigzag_XY(2, 1, 2, 2, 'r')

agi_comp = 0.01
agi_Vs = [0.2, -0.2]

# If already calibrated theta
skip_calibrate_theta = False
if skip_calibrate_theta:
    # TODO: query meas IV now?
    theta_pattern_tilled = -0.05113669581916014
    input('Use theta_pattern_tilled: {}'.format(theta_pattern_tilled))

d_X, d_Y = cur_params.execute('SELECT d_X, d_Y FROM masks WHERE mask=?',
                              (mask,)).fetchone()


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

    suss.velocity = 25
    suss.separate()
    suss.velocity = 1

    if not skip_calibrate_theta:
        # Calibrate theta
        delta_X = X_max - X_min
        delta_Y = Y_max - Y_min
        if delta_X == 0 and delta_Y == 0:
            input('calibrate theta to 0 mannually.')
            theta_pattern_tilled = 0
        else:
            if delta_X == 0:
                theta_diagonal_true = 90
            else:
                theta_diagonal_true = math.atan((delta_Y*d_Y) / (delta_X*d_X)) * 180 / math.pi
            if debug_mode:
                theta_diagonal_tilled = theta_diagonal_true + random.gauss(0, 3)
            else:
                input('Set X{}Y{} as home.'.format(X_min, Y_min))
                suss.move_to_xy_from_home(- delta_X * d_X, - delta_Y * d_Y)
                input('Right click X{} Y{}, press enter.'.format(X_max, Y_max))
                (x99_tilled, y99_tilled, _) = suss.read_xyz('H')
                theta_diagonal_tilled = math.atan(y99_tilled / x99_tilled) * 180 / math.pi
            theta_pattern_tilled = theta_diagonal_tilled - theta_diagonal_true
            print('theta_pattern_tilled:', theta_pattern_tilled)

    # Measure I-Vs.  Be sure separate!
    for mesa in mesas:
        print('mesa:', mesa)
        m_x_probe, m_y_probe = \
            cur_params.execute('SELECT xm_probe, ym_probe \
                                FROM mesas WHERE mask=? AND mesa=?',
                                (mask, mesa,)).fetchone()
        # TODO: xm ym exceptions
        for (X, Y) in dicXYs[mesa]:
            print('X{}Y{}'.format(X, Y))
            #if not first_measurement:
            #    suss.align()  # Already separate if first
            s_x_next = m_x_probe + (X-1)*d_X
            s_y_next = m_y_probe + (Y-1)*d_Y
            (x_next_from_home, y_next_from_home) = \
                rotate_vector(-s_x_next, -s_y_next, theta_pattern_tilled)
            suss.move_to_xy_from_home(x_next_from_home, y_next_from_home)
            suss.contact()
            if first_measurement and mesa == mesas[0]:
                input('Contact the prober.')
                first_measurement = False
            for V in agi_Vs:
                t0 = int(time.strftime('%Y%m%d%H%M%S'))  # 20150830203015
                Vs, Is, aborted = agi.double_sweep_from_zero(2, 1, V, None, agi_comp)
                points = len(Vs)
                # XY offset: UPDATE params SET X=X+8, Y=Y+12 WHERE sample="E0339 X9-12 Y13-16" and mesa="D56.3"
                cur_params.execute('INSERT INTO IV_params(t0,sample,X,Y,mesa,status,measPoints,compliance,voltage,instrument) \
                                    VALUES(?,?,?,?,?,?,?,?,?,?)',
                                   (t0, sample, X, Y, mesa,
                                    255, points, agi_comp, V, 'SUSS PA300 + Agilent 4156C')
                                  )
                tmp = zip([t0] * points, Vs, Is)  # [(t0, V0, I0), (t0, V1, I1), ...]
                cur_IVs.executemany('''INSERT INTO IVs(t0, V, I) VALUES(?, ?, ?)''', tmp)
                conn_params.commit()
                conn_IVs.commit()
                if debug_mode:
                    time.sleep(1)  # To avoid duplicates of "t0" in database
                if aborted:
                    break
            suss.align()
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
