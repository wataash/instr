# Std libs
import os
import sqlite3
import time
# Non-std libs
import visa
# My libs
from lib.keithley import Keithley2636A
from lib.sci9700 import Sci9700
from lib.algorithms import log_list


## Configurations ---------------------------------------------------------------
debug_mode = False  # Set True while development without instruments.
#sci_rsrc_name = 'GPIB0::1::INSTR'
#sci_timeout_sec = 1
ke_rsrc_name = 'GPIB0::26::INSTR'
sci_rsrc_name = 'GPIB0::1::INSTR'
ke_timeout_sec = 30
sci_timeout_sec = 1

sqlite3_file_name = os.path.expanduser('~') + '/Documents/instr_data/IT.sqlite3'

sample = 'E0339 X12Y15 D169'

voltage = 10e-3
compliance = 100e-6

instrument = '304B Keithley 2636A'
comment = None

# Initialize -------------------------------------------------------------------
if debug_mode:
    ap_rsrc = None
    ke_rsrc = None
    sci_rsrc = None
else:
    rm = visa.ResourceManager()
    print(rm.list_resources())
    ke_rsrc = rm.open_resource(ke_rsrc_name)
    sci_rsrc = rm.open_resource(sci_rsrc_name)

ke = Keithley2636A(ke_rsrc, ke_timeout_sec, debug_mode)
sci = Sci9700(sci_rsrc, sci_timeout_sec, debug_mode)


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
    ke.read_single_on(voltage, compliance)
    while(True):
        pass
        new_t = int(time.strftime('%Y%m%d%H%M%S'))
        if new_t == t:
            # for SQL unique constraint.
            time.sleep(1)
            new_t = int(time.strftime('%Y%m%d%H%M%S'))
        t = new_t
        
        temp = sci.read_temp('A')
        I = ke.read_single_read()
        points += 1
        cursor.execute('INSERT INTO IT VALUES(?,?,?,?)',
                       (t, t0, temp, I))
        sqlite3_connection.commit()

finally:
    cursor.execute('UPDATE params SET points=? WHERE t0=?',(points, t0))
    ke.read_single_off()
    sqlite3_connection.commit()
    cursor.close()

