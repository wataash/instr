from datetime import datetime
import time

import matplotlib.pyplot as plt

from instr.base import SourceMeter
from lib.database import Database


def meas_vi_double(srcmtr, db, sample, mesa, X, Y, instrument,
                   v_end, v_step=1e-3, v_points=None, i_limit=1e-3):
    """
    Sweep 0V -> v_end -> 0V and instert into database.
    Does not commit.

    :type srcmtr: SourceMeter
    :type db: Database
    :type mesa: str
    :type X: int
    :type Y: int
    :type instrument: str
    :return: vis, aborted
    :rtype: np.ndarray, bool
    """
    dt = datetime.utcnow().replace(microsecond=0)
    VIs, aborted = srcmtr.iv_sweep_double(v_end, v_step, v_points, i_limit)
    db.insert_vis(sample, mesa, X, Y, dt, len(VIs), i_limit, v_end,
                  instrument, VIs)
    return VIs, aborted


if __name__ == '__main__':
    import visa
    import lib.constants as c

    sample = 'dummy_sample'
    mesa = 'dummy_mesa'
    X = 6
    Y = 8
    input('{} X{} Y{} {}?'.format(sample, X, Y, mesa))

    limit_i = 0.010
    vs = [1, -1]  # Sweep voltages

    debug_mode = False

    # Setup --------------------------------------------------------------------
    if debug_mode:
        sample = 'dummy_sample'
        raise NotImplementedError

    db = Database(**c.mysql_config)

    rm = visa.ResourceManager()
    print(rm.list_resources())

    # from instr.agilent4156c import Agilent4156C
    # rsrc = rm.open_resource('GPIB0::18::INSTR')
    # srcmtr = Agilent4156C(rsrc=rsrc)
    # inst = 'Agilent 4156C'
    # v_points, i_limit = 1001, 1e-3

    from instr.ke2636a import Keithley2636A
    # rsrc = rm.open_resource('TCPIP::169.254.000.001::INSTR')
    rsrc = rm.open_resource('visa://169.254.136.196/GPIB0::20::INSTR')
    srcmtr = Keithley2636A(rsrc=rsrc)
    srcmtr.smu = 'a'
    inst = 'Keithley 2636A'
    v_points, i_limit = 101, 1e-3

    for v in vs:
        print('Measure {}...'.format(v))
        vis, aborted = meas_vi_double(srcmtr, db, sample, mesa, X, Y, inst,
                                      v, v_points=v_points, i_limit=i_limit)
        vs, Is = vis.transpose()
        plt.subplot(121)
        plt.plot(vs, Is, 'o-')  # TODO RV, multi-thread
        plt.subplot(122)
        plt.plot(vs, vs/Is, 'o-')  # TODO RV, multi-thread
        plt.show()
        time.sleep(1)
        db.cnx.commit()
        print('Commited.')
        if debug_mode:
            time.sleep(1)  # To avoid duplicates of "t0" in database
        if aborted:
            break
    # TODO update fitR3
    pass  # Breakpoint
