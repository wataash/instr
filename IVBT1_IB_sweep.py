# Std libs
import os
import sqlite3
import time
# Non-std libs
import visa
# My libs
from lib.ap1628t2 import AP1628T2
from lib.keithley import Keithley2636A
from lib.algorithms import log_list

## Configurations ---------------------------------------------------------------
debug_mode = False  # Set True while development without instruments.
#sci_rsrc_name = 'GPIB0::1::INSTR'
#sci_timeout_sec = 1
ap_rsrc_name = 'GPIB0::3::INSTR'
ap_timeout_sec = 1
ke_rsrc_name = 'GPIB0::26::INSTR'
ke_timeout_sec = 30

sqlite3_file_name = os.path.expanduser('~') + '/Documents/instr_data/IB.sqlite3'

sample = 'E0339 X12Y15 D169'

voltage = 10e-3
compliance = 100e-6

instrument = '304B Keithley 2636A'
comment = None

# Initialize -------------------------------------------------------------------
if debug_mode:
    ap_rsrc = None
    ke_rsrc = None
else:
    rm = visa.ResourceManager()
    print(rm.list_resources())
    ap_rsrc = rm.open_resource(ap_rsrc_name)
    ke_rsrc = rm.open_resource(ke_rsrc_name)

ap = AP1628T2(ap_rsrc, ap_timeout_sec, debug_mode)
ke = Keithley2636A(ke_rsrc, ke_timeout_sec, debug_mode)


# Connect to database ----------------------------------------------------------
sqlite3_connection = sqlite3.connect(sqlite3_file_name)
cursor = sqlite3_connection.cursor()


# Measure ----------------------------------------------------------------------
try:
    t0 = int(time.strftime('%Y%m%d%H%M%S'))
    cursor.execute('INSERT INTO params VALUES(?,?,?,?,?,?,?)',
                   (t0, sample, None, voltage, compliance, instrument, comment))
    sqlite3_connection.commit()

    t = t0
    points = 0
    G_list = log_list(10000, 1, 100) + [0] + log_list(-1, -10000, 100) + \
             log_list(-10000, -1, 100) + [0] + log_list(1, 10000, 100)
    G_list = list(reversed(range(-10000, 10000 + 1, 100))) + list(range(-10000, 10000 + 1, 100))
    ke.read_single_on(voltage, compliance)
    for G in G_list:
        new_t = int(time.strftime('%Y%m%d%H%M%S'))
        if new_t == t:
            # for SQL unique constraint.
            time.sleep(1)
            new_t = int(time.strftime('%Y%m%d%H%M%S'))
        t = new_t
        
        set_G = ap.out_gauss(G)
        I = ke.read_single_read()
        points += 1
        cursor.execute('INSERT INTO IB VALUES(?,?,?,?)',
                       (t, t0, set_G, I))
        sqlite3_connection.commit()

finally:
    cursor.execute('UPDATE params SET points=? WHERE t0=?',(points, t0))
    ke.read_single_off()
    ap.out_gauss(0)
    sqlite3_connection.commit()
    cursor.close()

