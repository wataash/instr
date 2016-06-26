from itertools import product
import time

import lib.algorithms as al
import lib.constants as c
from lib.database import Database, update_fit_R3
from instr.agilent4156c import Agilent4156C
from instr.suss_pa300 import SussPA300
from vi_meas import meas_vi_double

# Configurations ---------------------------------------------------------------
sample = 'dummy_sample'
inst = 'suss_test'
# inst = 'suss_BD_test'
# inst = 'suss'
debug_mode = False  # Set True during development without instruments.


agi_comp = 0.010  # Compliance (A)
agi_Vs = [0.3, -0.3]  # Sweep voltages for suss_test
# agi_Vs = [1.5, -1.5]  # Sweep voltages for suss_BD_test
# agi_Vs = [1.0, -1.0]  # Sweep voltages for suss

# Setup ------------------------------------------------------------------------
if debug_mode:
    sample = 'dummy_sample'
if not debug_mode:
    import visa

db_rds = Database(**c.mysql_config)
db_read = Database(user='readonly', database='master_db')

sql = ('SELECT mask, dX, dY, Xmin, Xmax, Ymin, Ymax FROM v02_sample '
       'WHERE sample=%s')
mask, dX, dY, X_min, X_max, Y_min, Y_max = db_rds.q_row_abs(sql, (sample,))

# XYs = spiral_XYs(X_min, X_max, Y_min, Y_max)
XYs = list(product(range(X_min, X_max+1), range(Y_min, Y_max+1)))
XYs = sorted(XYs, key=lambda x: (x[1], x[0]))

sql = ('SELECT mesa_id, xm_probe, ym_probe FROM v03_sample_mesa '
       'WHERE sample=%s')
dat_xypr_default = db_rds.q_all(sql, (sample,))
dic_mesaid_xypr_default = {mesa_id: xy for mesa_id, *xy in dat_xypr_default}

sql = ('SELECT mesa_id, xm_probe, ym_probe FROM suss_xm_ym '
       'WHERE sample=%s')
dat_xypr_spec = db_rds.q_all(sql, (sample,))
dic_mesaid_xypr_spec = {mesa_id: xy for mesa_id, *xy in dat_xypr_spec}

sql = 'SELECT mesa_id, mesa FROM mesa WHERE mask=%s'
dat_mesa = db_rds.q_all_abs(sql, (mask,))
dic_mesaid_mesa = {mesa_id: mesa for mesa_id, mesa in dat_mesa}

if debug_mode:
    agi = Agilent4156C(False)
    suss = SussPA300()
else:
    rm = visa.ResourceManager()
    print(rm.list_resources())
    agi_rsrc = rm.open_resource('GPIB0::18::INSTR')
    suss_rsrc = rm.open_resource('GPIB0::7::INSTR')
    agi = Agilent4156C(False, rsrc=agi_rsrc)
    suss = SussPA300(rsrc=suss_rsrc)

# Measure ----------------------------------------------------------------------
first_measurement = True
resp = input('Approaching to z_separate!\n')
if resp != 'yes':
    exit()
suss.approach_separate()

# Measure I-Vs.  Be sure separate!
mesa_ids = sorted(dic_mesaid_xypr_default)
for mesa_id in mesa_ids:
    print('{} (mesa_id {})'.format(dic_mesaid_mesa[mesa_id], mesa_id))
    if mesa_id in [1, 2, 5, 6, 7, 8]:
        print('Skip mesa.')
        continue
    for (X, Y) in XYs:
        if first_measurement and sample == 'dummy_sample' and \
                not (mesa_id == 3 and (X, Y) == (3, 4)):
            print('({},{})'.format(X, Y), end=' ')
            continue
        if inst != 'suss_test':
            sql = ('SELECT suss_R2 FROM v04_device '
                   'WHERE sample=%s AND mesa_id=%s AND X=%s AND Y=%s')
            R2 = db_read.q_single_abs(sql, (sample, mesa_id, X, Y,))
            if al.num_9th(R2) < 1.5:
                print('NG({},{})'.format(X, Y), end=' ')
                continue
        print('X{}Y{}'.format(X, Y))
        if mesa_id in dic_mesaid_xypr_spec:
            xs = dic_mesaid_xypr_spec[mesa_id][0] + (X - X_min) * dX
            ys = dic_mesaid_xypr_spec[mesa_id][1] + (Y - Y_min) * dY
        else:
            xs = dic_mesaid_xypr_default[mesa_id][0] + (X - X_min) * dX
            ys = dic_mesaid_xypr_default[mesa_id][1] + (Y - Y_min) * dY
        suss.safe_move_contact('H', -xs, -ys)
        if first_measurement:
            input('Contact the prober.')
            first_measurement = False
        for V in agi_Vs:
            mesa = dic_mesaid_mesa[mesa_id]
            print('Measure {}...'.format(V))
            # vis, aborted = meas_vi_double(agi, db, sample, mesa, X, Y,
            #                               'SUSS PA300 + Agilent 4156C',
            #                               V, v_points=101, i_limit=10e-3)
            # TODO hard code
            vis, aborted = meas_vi_double(agi, db_rds, sample, mesa, X, Y,
                                          inst,
                                          V, v_points=101, i_limit=agi_comp)
            # time.sleep(3)  # wait replication TODO test
            # update_fit_R3(db_read, db, sample, mesa, X, Y)  # TODO test
            db_rds.cnx.commit()
            print('Committed.')
            if debug_mode:
                time.sleep(1)  # To avoid duplicates of "t0" in database
            if aborted:
                break

suss.separate_separate()
input('Done.')
pass  # Breakpoint
