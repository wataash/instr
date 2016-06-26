from datetime import datetime
from multiprocessing.pool import ThreadPool
from os.path import expanduser
from shutil import copy2
from tempfile import gettempdir

import numpy as np
import visa

from instr.ap1628t2 import AP1628T2
from instr.ke2636a import Keithley2636A


room = 'debug'
if room == 'debug':
    ap = AP1628T2(None)
    ke = Keithley2636A(None)
else:
    if room == 'room1':
        ap_rsrc_name = 'GPIB0::3::INSTR'
        ke_rsrc_name = 'GPIB0::26::INSTR'
        # ke_timeout_sec = 30
    elif room == 'room2':
        ap_rsrc_name = ''
        ke_rsrc_name = ''
    else:
        raise RuntimeError

    rm = visa.ResourceManager()
    print(rm.list_resources())
    ap = AP1628T2(rm.open_resource(ap_rsrc_name))
    ke = Keithley2636A(rm.open_resource(ke_rsrc_name))

save_dir = expanduser('~/Desktop/')
backup_dir = gettempdir() + '/'
path_tHIs = save_dir + 'tHIs.csv'
path_tIHs = save_dir + 'tIHs.csv'
voltage = 10e-3
i_limit = 1e-3

try:
    # 100oe/s, +-100oe, 1s/100oe, 4s
    ap.sweep(100, unit='Oe')
    Hs = [0, -100, 0, 100]
    speed = 100
    duration = 0.1

    # 1000 Oe/s, +-10000 Oe, 5000 Oe/5 s x 8 --> 40 s
    # ap.sweep(10000, unit='Oe')
    # Hs = [5000, 0, -5000, -10000, -5000, 0, 5000, 10000]
    # speed = 1000

    # 100 Oe/s, +-1000 Oe, 5000 Oe/5 s x 8 --> 40 s
    # ap.sweep(1000, unit='Oe')
    # Hs = [500, 0, -500, -1000, -500, 0, 500, 1000]
    # speed = 100

    # tHIs = pd.DataFrame(columns=['Time (s)', 'H (Oe)', 'I (A) (interpolated)'])
    # tIHs = pd.DataFrame(columns=['Time (s)', 'I (A)', 'H (Oe) (interpolated)'])
    tHIs = np.array([], dtype=np.float64).reshape((0, 3))  # I: interpolation
    tIHs = np.array([], dtype=np.float64).reshape((0, 3))  # H: interpolation
    pool = ThreadPool(processes=2)  # for ap and ke
    dt0 = datetime.now()
    for H in Hs:
        time_offset = (datetime.now() - dt0).total_seconds()

        async_result_ap = pool.apply_async(ap.sweep, (H,),
                                           {'speed':speed, 'unit':'Oe'})
        async_result_ke = pool.apply_async(ke.time_sampling)  # TODO                                           {'speed':speed*0.6, 'unit':'Oe'})
        tIs = np.array(async_result_ke.get())
        tHs = np.array(async_result_ap.get())

        tHs[:,0] += time_offset
        tIs[:,0] += time_offset
        # Is_interp = np.interp(tHs[:,0], tIs[:,0], tIs[:,1],
        #                       left=np.nan, right=np.nan)
        Is_interp = np.interp(tHs[:,0], tIs[:,0], tIs[:,1])
        Hs_interp = np.interp(tIs[:,0], tHs[:,0], tHs[:,1])
        new_tHIs = np.column_stack((tHs, Is_interp))
        new_tIHs = np.column_stack((tIs, Hs_interp))
        tHIs = np.vstack((tHIs, new_tHIs))
        tIHs = np.vstack((tIHs, new_tIHs))

        # HEADER dt0, voltage, ilimit, inst, comment
        np.savetxt(path_tHIs, tHIs, delimiter=', ',
                   header='Time(s), H(Oe), I_interp(A)', comments='')
        np.savetxt(path_tIHs, tIHs, delimiter=', ',
                   header='Time(s), I(A), H_interp(Oe)', comments='')
    copy2(path_tHIs, backup_dir + 'tHIs_' + str(dt0).replace(':', '-') +'.csv')
    copy2(path_tIHs, backup_dir + 'tIHs_' + str(dt0).replace(':', '-') +'.csv')
finally:
    ap.sweep(0)
    ke.off()  # TODO
