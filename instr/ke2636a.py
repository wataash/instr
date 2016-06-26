import numpy as np
import unittest2

from instr.base import SourceMeter


class Keithley2636A(SourceMeter):
    def __init__(self, rsrc=None, timeout_sec=600, reset=True):
        self._smu = 'a'
        idn = 'Keithley Instruments Inc., Model 2636A'
        super().__init__(rsrc, idn, timeout_sec, reset)

    @property
    def smu(self):
        return self._smu

    @smu.setter
    def smu(self, value):
        if value not in ['a', 'b']:
            raise ValueError
        self._smu = value

    def check_error(self):
        if self._debug_mode:
            super().check_error()
        tmp = self.q('print(errorqueue.next())')
        if tmp != '0.00000e+00\tQueue Is Empty\t0.00000e+00\n':
            raise RuntimeError('Error on Keithley 2636A.')

    def reset(self):
        self.w('reset()', True)
        # self.w('smua.reset(); smub.reset()', True)

    def iv_sweep(self, v_start=0.0, v_end=10e-3, v_step=1e-3,
                 v_points=None, i_limit=1e-6, settle_time=0.0, reset=True):
        """
        Reference manual 3-31
        TODO: when aborted?

        :return: vis, is_aborted
        """
        if reset:
            self.reset()

        if v_points is None:
            v_points = self._v_step_to_points(v_start, v_end, v_step)

        lim = 'smu{}.source.limiti = {}'.format(self.smu, i_limit)
        self.w(lim, True)

        meas = 'SweepVLinMeasureI(smu{}, {}, {}, {}, {})'. \
            format(self.smu, v_start, v_end, settle_time, v_points)
        self.w(meas, True)

        prnt = 'printbuffer(1, {}, smu{}.nvbuffer1.readings)'. \
            format(v_points, self.smu)
        resp = self.q(prnt, True)
        Is = resp.split(', ')
        Is = np.asarray(Is, np.float64)
        if len(Is) != v_points:
            aborted = True
            v_points = len(Is)
        else:
            aborted = False
        vs = np.linspace(v_start, v_end, v_points)

        vis = np.array([vs, Is]).transpose()
        return vis, aborted

    def iv_sweep_double(self, v_max, v_step=1e-3, v_points=None,
                        i_limit=1e-3, settle_time=0.0, reset=True):
        vis1, aborted = self.iv_sweep(0, v_max, v_step,
                                      v_points, i_limit, settle_time, reset)
        if aborted:
            return vis1, aborted
        vis2, aborted = self.iv_sweep(v_max, 0, v_step,
                                      v_points, i_limit, settle_time, reset)

        ret = np.concatenate((vis1, vis2))
        return ret, aborted


class TestKeithley2636A(unittest2.TestCase):
    def test_iv_sweep(self):
        import matplotlib.pyplot as plt
        ke2636a.reset()
        v_start = 0.0
        v_end = 1e-3

        self.smu = 'a'


        vis, aborted = \
            ke2636a.iv_sweep(v_start, v_end, v_step=v_end / 10, i_limit=1e-9)
        plt.plot(*vis.transpose(), 'o-')
        plt.show()

        vis, aborted = \
            ke2636a.iv_sweep(v_start, v_end, v_points=101, i_limit=1e-6)
        plt.plot(*vis.transpose(), 'o-')
        plt.show()

        # v_step ignored
        vis, aborted = \
            ke2636a.iv_sweep(v_start, v_end, v_step=1, v_points=11)
        plt.plot(*vis.transpose(), 'o-')
        plt.show()

        vis, aborted = ke2636a.iv_sweep_double(10e-3)
        plt.plot(*vis.transpose(), 'o-')
        plt.show()

        self.smu = 'b'
        vis, aborted = ke2636a.iv_sweep(v_start, v_end, v_points=11)
        plt.plot(*vis.transpose(), 'o-')
        plt.show()


if __name__ == '__main__':
    import visa

    rm = visa.ResourceManager()

    # ke2636a_rsrc = rm.open_resource('visa://169.254.136.196/GPIB0::20::INSTR')
    ke2636a_rsrc = rm.open_resource('TCPIP::169.254.000.001::INSTR')
    ke2636a = Keithley2636A(ke2636a_rsrc)

    unittest2.main()

    pass
