import numpy as np
import unittest2
import visa

from instr.base import SourceMeter


# TODO compliance

class Agilent4156C(SourceMeter):
    def __init__(self, use_us_commands=False, gnd_smu=2, bias_smu=1,
                 rsrc=None, timeout_sec=600, reset=True):
        self._gnd_smu = gnd_smu
        self._src_smu = bias_smu
        idn = 'HEWLETT-PACKARD,4156C'
        super().__init__(rsrc, idn, timeout_sec, reset)
        self._use_us_commands = use_us_commands
        self._integration_time = 'SHOR'

    def check_error(self):
        """
        >>> a = Agilent4156C()
        debug mode (Agilent4156C): skip BaseInstr.__init__.
        >>> a.check_error()
        debug mode (Agilent4156C): skip check_error.
        """
        if self._debug_mode:
            super().check_error()
            return
        tmp = self.q("SYST:ERR?")
        tmp = tmp.split(',')
        if tmp[0] != '+0':
            raise RuntimeError('Error on Agilent 4156C.')

    def reset(self):
        """
        >>> a = Agilent4156C()
        debug mode (Agilent4156C): skip BaseInstr.__init__.
        >>> a.reset()
        debug mode (Agilent4156C): skip reset.
        debug mode (Agilent4156C): skip check_error.
        """
        if self._debug_mode:
            super().reset()
            return
        self.w('*RST')  # Restore default configuration
        self.w('*CLS')  # Clear query buffer
        self.check_error()

    @property
    def integration_time(self):
        return self._integration_time

    @integration_time.setter
    def integration_time(self, value):
        if value not in ['SHOR', 'MED', 'LONG']:
            raise ValueError("integ_time: 'SHOR' or 'MED', 'LONG'")
        self._integration_time = value
        self.w(":PAGE:MEAS:MSET:ITIM {}".format(self._integration_time))
        self.check_error()

    def _disable_all_units(self, *except_units):
        if self._debug_mode:
            self._dbg_print_skip_method()
            return
        if self._use_us_commands:
            raise NotImplementedError
        else:
            units = ["SMU1", "SMU2", "SMU3", "SMU4",
                     "VSU1", "VSU2", "VMU1", "VMU2"]
            for i in range(8):
                if (i + 1) in except_units:
                    continue
                self.w(":PAGE:CHAN:{}:DIS".format(units[i]))
        self.check_error()

    def _configure_smu(self, smu_num, mode, func, V_name=None, I_name=None):
        """
        >>> a = Agilent4156C()
        debug mode (Agilent4156C): skip BaseInstr.__init__.

        >>> a._configure_smu(1, 2, 2)
        debug mode (Agilent4156C): skip w.
        debug mode (Agilent4156C): skip check_error.

        :param smu_num: 1234
        :param mode: 1: V, 2: I, 3: common
        :param func: 1: VAR1, 2: VAR2, 3: CONSTANT, 4: VAR1'
        :param V_name: Default: 'V{smu_num}'
        :param I_name: Default: 'I{smu_num}'
        """
        if smu_num not in [1, 2, 3, 4]:
            raise ValueError('invalid smu_num')

        if V_name is None:
            V_name = 'V' + str(smu_num)
        if I_name is None:
            I_name = 'I' + str(smu_num)

        if self._use_us_commands:
            raise NotImplementedError
        else:
            _mode = ('V', 'I', 'COMM')[mode - 1]
            _func = ('VAR1', 'VAR2', 'CONS', 'VARD')[func - 1]

            self.w(":PAGE:CHAN:SMU{}:VNAM '{}';INAM '{}';MODE {};FUNC {};".
                   format(smu_num, V_name, I_name, _mode, _func))
        self.check_error()

    def _set_user_func(self, name, unit, definition):
        # TODO property, overridden by others?
        self.w(":page:chan:ufun:def '{}','{}','{}'".
               format(name, unit, definition))
        self.check_error()

    def _set_Y(self, Y1_name, Y1_log_scale=False,
               Y2_name=None, Y2_log_scale=False):
        # TODO property
        if self._debug_mode:
            self._dbg_print_skip_method()
        if self._use_us_commands:
            raise NotImplementedError
        else:
            self.w(":PAGE:DISP:GRAP:Y1:NAME '{}';".format(Y1_name))
            if Y2_name is not None:
                self.w(":PAGE:DISP:GRAP:Y2:NAME '{}';".format(Y2_name))
            if Y1_log_scale:
                self.w(":PAGE:DISP:GRAP:Y1:SCAL LOG;")
            if Y2_log_scale:
                self.w(":PAGE:DISP:GRAP:Y2:SCAL LOG;")
        self.check_error()

    def configure_display_limit(self, x_min, x_max,
                                y1_min=1e-12, y1_max=1e-3,
                                y2_min=1e3, y2_max=1e12):
        """
        Execute _set_Y before.
        """
        # TODO property
        if self._debug_mode:
            print('debug: skip configure_display')
        if self._use_us_commands:
            raise NotImplementedError
        else:
            self.w(":PAGE:DISP:SET:GRAP:X:MIN {};".format(x_min))
            self.w(":PAGE:DISP:SET:GRAP:X:MAX {};".format(x_max))
            self.w(":PAGE:DISP:SET:GRAP:Y1:MIN {};".format(y1_min))
            self.w(":PAGE:DISP:SET:GRAP:Y1:MAX {};".format(y1_max))
            self.w(":PAGE:DISP:SET:GRAP:Y2:MIN {};".format(y2_min))
            self.w(":PAGE:DISP:SET:GRAP:Y2:MAX {};".format(y2_max))
        self.check_error()

    def contact_test(self, time_interval_second=10e-3, reset=True,
                     applyV=1e-3, compI=10e-3, meas_time_second=60, points=0):
        """
        Returns float[] times, float[] currents
        :rtype: list of float, list of float
        """
        if reset:
            self.w('*RST')
        if self._debug_mode:
            raise NotImplementedError
        if points == 0:
            points = int(meas_time_second / time_interval_second)
        # 8000: OK, 8500: "ERROR 7: DATA buffer full. Too many points."
        points = min(8000, points)
        if self._use_us_commands:
            raise NotImplementedError
        else:
            self.w(":PAGE:CHAN:MODE SAMP;")  # not in GPIB mannual damn
        self._disable_all_units(self._gnd_smu, self._src_smu)
        self._configure_smu(self._gnd_smu, 3, 3)
        self._configure_smu(self._src_smu, 1, 3)
        if self._use_us_commands:
            raise NotImplementedError
        else:
            self.w(":PAGE:MEAS:SAMP:IINT {};POIN {};".
                   format(time_interval_second, points))
            self.w(":PAGE:MEAS:SAMP:CONS:SMU{} {};".
                   format(self._src_smu, applyV))
            self.w(":PAGE:MEAS:SAMP:CONS:SMU{}:COMP {};".
                   format(self._src_smu, compI))
        self._set_user_func('R', 'ohm', 'V{0}/I{0}'.format(self._src_smu))
        self._set_Y("I{}".format(self._src_smu), True, 'R', True)
        self.configure_display_limit(0, meas_time_second, 1e-15, 1e-3, 1, 1000)
        if self._use_us_commands:
            raise NotImplementedError
        else:
            self.w(":PAGE:MEAS:MSET:ITIM MED;")  # fixed
            self.w(":PAGE:SCON:SING")
            self.q('*OPC?')
            resp = self.q(":FORM:DATA ASC;:DATA? '@TIME';")
            times = [float(t) for t in resp.split(',') if float(t) != 9.91e307]
            resp = self.q(":FORM:DATA ASC;:DATA? 'I{}';".format(self._src_smu))
            currents = [float(I) for I in resp.split(',') if
                        float(I) != 9.91e307]
            if len(times) != len(currents):
                raise RuntimeError
            return times, currents

    def iv_sweep(self, v_start, v_end, v_step=1e-3, v_points=None,
                 i_limit=1e-3, reset=True):
        raise NotImplementedError()

    def iv_sweep_double(self, v_max, v_step=1e-3, v_points=None, i_limit=10e-3):
        """

        :param v_points: in single direction
        """
        if v_points is not None:
            v_step = self._v_points_to_step(0, v_max, v_points)
        else:
            v_points = self._v_step_to_points(0, v_max, v_step)

        if v_points > 1001:
            raise RuntimeError('Number of step exceeds 1001. '
                               '(see the manual of 4156C)')

        if self._debug_mode:
            return super().iv_sweep_double(v_max, v_step, v_points, i_limit)

        self._disable_all_units(self._gnd_smu, self._src_smu)
        self._configure_smu(self._gnd_smu, 3, 3)
        self._configure_smu(self._src_smu, 1, 1)

        is_P = v_max > 0  # is positive sweep
        if not is_P:
            v_step = -v_step

        if self._use_us_commands:
            raise NotImplementedError
        else:
            self.w(":PAGE:MEAS:VAR1:MODE DOUB;")
            self.w(":PAGE:MEAS:SWE:VAR1:STAR 0")
            self.w(":PAGE:MEAS:VAR1:STOP {};".format(v_max))
            self.w(":PAGE:MEAS:VAR1:STEP {};".format(v_step))
            # TODO: hold time, deley time
            # TODO: stop at abnormal

        self._set_user_func('R', 'ohm', 'V{0}/I{0}'.format(self._src_smu))
        self._set_Y("I{}".format(self._src_smu), True, 'R', True)
        self.configure_display_limit(0 if is_P else v_max,
                                     v_max if is_P else 0,
                                     1e-12 if is_P else -1e-3,
                                     1e-3 if is_P else -1e-12,
                                     1e3, 1e12)
        self.w(':PAGE:SCON:MEAS:SING')
        self.q('*OPC?')
        resp = self.q(":FORM:DATA ASC;:DATA? 'V{}';".format(self._src_smu))
        vs = np.asarray(resp.split(','), np.float64)
        resp = self.q(":FORM:DATA ASC;:DATA? 'I{}';".format(self._src_smu))
        Is = np.asarray(resp.split(','), np.float64)
        vs = vs[vs != 9.91e307]
        aborted = len(vs) != len(Is)
        Is = Is[Is != 9.91e307]
        if len(vs) != len(Is):
            raise Exception
        vis = np.array([vs, Is]).transpose()
        return vis, aborted


class TestAgilent4156C(unittest2.TestCase):
    def test_10_properties(self):
        a.reset()
        a.integration_time = 'MED'
        a.integration_time = 'SHOR'
        a.integration_time = 'LONG'
        with self.assertRaises(ValueError):
            a.integration_time = 'invalid'

    def test_20_configure(self):
        a.reset()
        a._disable_all_units(3)
        a._configure_smu(1, 2, 2, 'VV', 'II')
        a._set_user_func('R', 'Ohm', 'VV/II')
        a._set_user_func('R1000', 'Ohm', '1000*R')
        a._set_Y('II', False, 'R1000', True)
        a.configure_display_limit(-1, 1)

    def test_30_contact_test(self):
        a.contact_test()

    def test_40_iv_sweep_double(self):
        a.reset()
        resp = a.iv_sweep_double(0.1)
        self.assertIsInstance(resp, tuple)
        self.assertIsInstance(resp[0], list)
        self.assertIsInstance(resp[0][0], tuple)
        self.assertIsInstance(resp[0][0][0], float)
        self.assertIsInstance(resp[1], bool)
        print('Aborted:', resp[1])

        resp = a.iv_sweep_double(-0.1)
        print('Aborted:', resp[1])


if __name__ == '__main__':
    rm = visa.ResourceManager()
    a_rsrc = rm.open_resource('GPIB0::18::INSTR')
    a = Agilent4156C(use_us_commands=False, gnd_smu=2, bias_smu=1, rsrc=a_rsrc)

    unittest2.main()

    # a.contact_test()
    # a.double_sweep_from_zero(2, 1, 10e-3, 1e-3)
