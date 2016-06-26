import datetime
import time

import numpy as np
from progressbar import ProgressBar
import unittest2

from instr.base import BaseInstr


# TODO: consider hysteresis

class AP1628T2(BaseInstr):
    def __init__(self, rsrc, timeout_sec=3, reset=True):
        idn = 'TAKASAGO,AP-1628T,00000,Ver2.30Rev1.06\r\n'
        super().__init__(rsrc, idn, timeout_sec, reset=False)
        if self._debug_mode:
            self._analog_value_debug = 0

        # analong range +-32000: corresponding to +-1T
        # analog 1 = 1/32000 T = 0.03125 mT = 0.3125 Oe
        self.__analog_over_tesla = 32000
        self.__analog_over_oersted = 3.2

        # If change this value, be careful not to make abrupt change of
        # the magnetic field that causes electromagnetic induction.
        # Must be positive.
        # self._analog_step_max = 20  # 6.25Oe, 0.625mT
        self._analog_step_max = 100  # 31.25Oe, 3.125mT

        if reset:
            self.reset()

    @property
    def _analog_value(self):
        """
        Reads and the current value using GPIB command 'T1'.
        (see the vendor's manual p.34)
        Bug in AP: if value is -1 -> return 65535.
        """
        if self._debug_mode:
            time.sleep(0.020)  # GPIB communication time ~20ms
            return self._analog_value_debug
        resp = self.q('T1')  # 'A1D+00000,A2D+00000,A3D000,A4D000,A5D000,H0\r\n'
        ret = resp.split(',')[0]  # 'A1D+00000'
        ret = int(ret[4:])
        return ret

    @_analog_value.setter
    def _analog_value(self, value:int):
        """
        Sets analog value using GPIB command 'A1D'.
        (see the vendor's manual p.34)

        :param value: Analog value.
        """
        if not isinstance(value, int):
            raise TypeError('value must be integer.')
        if not -32000 <= value <= 32000:
            raise ValueError('value out of range.')
        current_value = self._analog_value
        if abs(value - current_value) > self._analog_step_max:
            raise ValueError('Exceeds maximum analog step. '
                             '(Too fast sweeping)')

        if value == -1:  # See the docstring in the getter.
            value = 0
        if self._debug_mode:
            time.sleep(0.020)  # GPIB communication time ~20ms
            self._analog_value_debug = value
        else:
            self.w('A1D{}'.format(value))
        current_value = self._analog_value
        if current_value != value:
            raise RuntimeError('Failed to set analog value.')

    def sweep(self, set_val:float, step=0.0, speed=0.0, unit='analog'):
        """
        If step==0 and speed==0 --> sweep in maximum step

        :param set_val: analog: -32000 to 32000
                        (-1T to 1T, -10000Oe to 10000Oe)
        :param speed: overrides step.
        :param unit: 'analog' or 'T' or 'Oe'
        :rtype: list of tuple(float, float)
        :return: [(t0, val0), (t1, val1), ...]  (t: seconds unit)
        """
        dt0 = datetime.datetime.now()

        if (step < 0) or (speed < 0):
            raise ValueError('step and step must be positive.')

        if unit == 'analog':
            pass
        elif unit == 'T':
            set_val *= self.__analog_over_tesla
            step *= self.__analog_over_tesla
            speed *= self.__analog_over_tesla
        elif unit == 'Oe':
            set_val *= self.__analog_over_oersted
            step *= self.__analog_over_oersted
            speed *= self.__analog_over_oersted
        else:
            raise ValueError("unit must be either 'analog', 'T', or 'Oe'.")

        if step == 0 and speed == 0:
            step = self._analog_step_max

        val_init = self._analog_value
        ascending = True if val_init <= set_val else False
        if not ascending:
            step = -step
            speed = -speed

        ret = []
        val = val_init
        pbar = ProgressBar().start()
        print('{} to {} ({}Oe to {}Oe)'.
              format(val_init, set_val,
                     val_init/self.__analog_over_oersted,
                     set_val/self.__analog_over_oersted))
        while val != set_val:
            t = (datetime.datetime.now() - dt0).total_seconds()
            if speed == 0 and ascending:
                val = min(set_val, val + step)
            elif speed == 0 and (not ascending):
                val = max(set_val, val + step)
            elif speed != 0 and ascending:
                val = min(set_val, val_init + int(speed*t))
            elif speed != 0 and (not ascending):
                val = max(set_val, val_init + int(speed*t))
            self._analog_value = int(val)
            ret.append((t, int(val)))

            # Max 99%;
            pbar.update(abs(val-val_init)/abs(set_val-val_init) * 100)
        pbar.finish()
        return ret

    def reset(self):
        # '*RST' is dengerous because it turn off the magnetic field abruptly.
        self.sweep(0, self._analog_step_max)
        self.q('*RST')

    def demagnetize(self):
        """Remove hysteresis"""
        raise NotImplementedError


class TestAP1628t2(unittest2.TestCase):
    def atest10_analog_value(self):
        ap.reset()
        print(ap._analog_value)
        ap._analog_value = 1
        ap._analog_value = -1
        with self.assertRaises(ValueError):
            ap._analog_value = 100
        with self.assertRaises(ValueError):
            ap._analog_value = 100000
        with self.assertRaises(TypeError):
            ap._analog_value = 0.0

    def atest20_sweep(self):
        import matplotlib.pyplot as plt

        ap.reset()
        tBs = ap.sweep(100, 10)
        # plt.plot(*(zip(*tBs)))
        # plt.show()

        ap.sweep(-20, 1, unit='Oe')
        ap.sweep(100, speed=20)
        ap.sweep(100, speed=20)
        with self.assertRaises(ValueError):
            ap.sweep(0, speed=10000)

    def test_benchmark_sweep(self):
        import cProfile

        ap.reset()
        cProfile.run('ap.sweep(100, step=1)')
        ap.reset()
        cProfile.run('ap.sweep(1000, step=10)')


if __name__ == '__main__':
    import visa

    # rm = visa.ResourceManager()
    # ap_rsrc = rm.open_resource('visa://169.254.3.201/GPIB0::1::INSTR')  # 300mK
    # ap_rsrc = rm.open_resource('visa://169.254.136.196/GPIB0::3::INSTR')  # 3K
    # ap = AP1628T2(ap_rsrc)
    ap = AP1628T2(None)

    try:
        unittest2.main()
    finally:
        ap.sweep(0)
    pass
