import math

from base_instr import BaseInstr


class Agilent4156C(BaseInstr):
    def __init__(self, instr_resource, timeout_sec, use_us_commands, debug_mode=False):
        self._debug_mode = debug_mode
        super().__init__(instr_resource, timeout_sec, self._debug_mode)
        self._use_us_commands = use_us_commands
        if debug_mode:
            return
        if self.q('*IDN?') != 'HEWLETT-PACKARD,4156C,0,03.10:04.08:01.00\n':
            raise RuntimeError('Failed to connect to Agilent 4156C.')
        self.w('*RST')  # Restore default configuration
        self.w('*CLS')  # Clear query buffer

    def configure_smu(self, smu_num, mode, func, V_name=None, I_name=None):
        """ Description here
        :param smu_num: 1234
        :param mode: 1: V, 2: I, 3: common
        :param func: 1: VAR1, 2: VAR2, 3: CONSTANT, 4: VAR1'
        :param V_name: Default: 'V{smu_num}'
        :param I_name: Default: 'I{smu_num}'
        :rtype: str
        """
        if not (smu_num == 1 or smu_num == 2 or smu_num == 3 or smu_num == 4):
            raise ValueError('invalid smu_num')
        if self._debug_mode:
            print('debug: skip configure_smu')
            return
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
        return self.q('SYST:ERR?')

    def disable_all_units(self, *except_units):
        """desc
        :param except_units: 1: SMU1, 2: SMU2, 3: SMU3, 4: SMU4, 5: VSU1, 6: VSU2, 7: VMU1, 8: VMU2
        :type except_units: tuple of int
        :rtype: str
        """
        if self._debug_mode:
            print('debug: skip disable_all_units')
        if self._use_us_commands:
            raise NotImplementedError
        else:
            units = ["SMU1", "SMU2", "SMU3", "SMU4", "VSU1", "VSU2", "VMU1", "VMU2"]
            for i in range(8):
                if (i + 1) in except_units:
                    continue
                self.w(":PAGE:CHAN:{}:DIS".format(units[i]))
        return self.q('SYST:ERR?')

    def set_Y2(self, Y2name, is_log_scale=False):
        """
        desc
        :param Y2name:
        :type Y2name: str
        :param is_log_scale:
        :type is_log_scale: bool
        :return:
        :rtype: str
        """
        if self._debug_mode:
            print('debug: skip set_Y2')
        if self._use_us_commands:
            raise NotImplementedError
        else:
            self.w(":PAGE:DISP:GRAP:Y2:NAME '{}';".format(Y2name))
            if is_log_scale:
                self.w(":PAGE:DISP:GRAP:Y2:SCAL LOG;")
        return self.q('SYST:ERR?')

    def configure_display(self, x_min, x_max, y1_min, y1_max, y2_min=1e-15, y2_max: str=10e-3):
        """
        desc
        :param x_min:
        :type x_min: float
        :param x_max:
        :type x_max: float
        :param y1_min:
        :type y1_min: float
        :param y1_max:
        :type y1_max: float
        :param y2_min:
        :type y2_min: float
        :param y2_max:
        :type y2_max: float
        :return:
        :rtype: str
        """
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
        return self.q('SYST:ERR?')

    def contact_test(self, gnd_smu, bias_smu, time_interval_second,
                     applyV=1e-3, compI=10e-3,
                     meas_time_second=60, points=0, y1min=0, y1max=1e-3):
        """
        Returns float[] times, float[] currents
        :param gnd_smu:
        :param bias_smu:
        :param time_interval_second:
        :param applyV:
        :param compI:
        :param meas_time_second:
        :param points:
        :param y1min:
        :param y1max:
        :return:
        :rtype: list of float, list of float
        """
        if self._debug_mode:
            print('Debug: return dummy data')
            return [[0,0.19,0.3,0.41,0.52,0.63,0.74,0.85,0.96,1.07,1.18,1.29,1.4,1.51,1.62,1.73,1.84,1.95,2.06,2.17,2.28,2.39,2.5,2.61,2.72,2.83,2.94,3.05,3.16,3.27,3.38,3.49,3.6,3.71,3.82,3.93,4.04,4.15,4.26,4.37,4.48,4.59,4.7,4.81,4.92,5.03,5.14,5.25,5.36,5.47,5.58,5.69,5.8,5.91,6.02,6.13,6.24,6.35,6.46,6.57,6.68,6.79,6.9,7.01,7.12,7.23,7.34,7.45,7.56,7.67,7.78,7.89,8,8.11,8.22,8.33,8.44,8.55,8.66,8.77,8.88,8.99,9.1,9.21,9.32,9.43,9.54,9.65,9.76,9.87,9.98,10.09,10.2,10.31,10.42,10.53,10.64,10.75,10.86,10.97],        [-1.84E-12,-1.57E-12,-1.51E-12,-1.48E-12,-1.48E-12,-1.5E-12,-1.43E-12,-1.46E-12,-1.4E-12,-1.42E-12,-1.46E-12,-1.43E-12,-1.42E-12,-1.41E-12,-1.44E-12,-1.41E-12,-1.44E-12,-1.41E-12,-1.43E-12,-1.4E-12,-1.43E-12,-1.41E-12,-1.39E-12,-1.41E-12,-1.4E-12,-1.4E-12,-1.39E-12,-1.37E-12,-1.39E-12,-1.4E-12,-1.35E-12,-1.41E-12,-1.4E-12,-1.4E-12,-1.37E-12,-1.38E-12,-1.35E-12,-1.38E-12,-1.38E-12,-1.41E-12,-1.42E-12,-1.4E-12,-1.4E-12,-1.4E-12,-1.33E-12,-1.32E-12,-1.37E-12,-1.32E-12,-1.34E-12,-1.37E-12,-1.35E-12,-1.37E-12,-1.36E-12,-1.34E-12,-1.34E-12,-1.34E-12,-1.34E-12,-1.33E-12,-1.32E-12,-1.33E-12,-1.36E-12,-1.38E-12,-1.37E-12,-1.35E-12,-1.35E-12,-1.33E-12,-1.37E-12,-1.34E-12,-1.38E-12,-1.33E-12,-1.34E-12,-1.38E-12,-1.34E-12,-1.36E-12,-1.36E-12,-1.36E-12,-1.35E-12,-1.39E-12,-1.4E-12,-1.36E-12,-1.37E-12,-1.38E-12,-1.39E-12,-1.41E-12,-1.39E-12,-1.38E-12,-1.33E-12,-1.34E-12,-1.34E-12,-1.33E-12,-1.35E-12,-1.35E-12,-1.42E-12,-1.4E-12,-1.37E-12,-1.33E-12,-1.37E-12,-1.34E-12,-1.31E-12,-1.38E-12]]
        if points == 0:
            points = int(meas_time_second / time_interval_second)
        points = min(8000, points)  # 8000: OK, 8500: "ERROR 7: DATA buffer full. Too many points."
        self.w('*RST')
        if self._use_us_commands:
            raise NotImplementedError
        else:
            self.w(":PAGE:CHAN:MODE SAMP;")  # not in GPIB mannual damn
        self.disable_all_units(gnd_smu, bias_smu)
        self.configure_smu(gnd_smu, 3, 3)
        self.configure_smu(bias_smu, 1, 3)
        if self._use_us_commands:
            raise NotImplementedError
        else:
            self.w(":PAGE:MEAS:SAMP:IINT {};POIN {};".format(time_interval_second, points))
            self.w(":PAGE:MEAS:SAMP:CONS:SMU{} {};".format(bias_smu, applyV))
            self.w(":PAGE:MEAS:SAMP:CONS:SMU{}:COMP {};".format(bias_smu, compI))
        self.set_Y2("I{}".format(bias_smu), True)
        self.configure_display(0, meas_time_second, y1min, y1max, 1e-12, 100e-6)  # 1 Gohm, 10 ohm at 1mV
        if self._use_us_commands:
            raise NotImplementedError
        else:
            self.w(":PAGE:MEAS:MSET:ITIM MED;")  # fixed
            self.w(":PAGE:SCON:SING")
            self.q('*OPC?')
            times = [float(t) for t in
                     self.q(":FORM:DATA ASC;:DATA? '@TIME';").split(',') if float(t) != 9.91e307]
            currents = [float(I) for I in self.q(":FORM:DATA ASC;:DATA? 'I{}';".format(bias_smu)).split(',') if
                        float(I) != 9.91e307]
            if len(times) != len(currents):
                raise RuntimeError
            return times, currents

    def double_sweep_from_zero(self, gnd_smu, swp_smu, end_V, step_V, display_I=10e-3, comp_I=10e-3):
        """
        You can write v, i, _ = double_sweep_from_zero(...).

        :param gnd_smu: SMU number for ground
        :type gnd_smu: int
        :param swp_smu: SMU number for bias
        :type swp_smu: int
        :param end_V: End voltage
        :type end_V: float
        :param step_V: Voltage step
        :type step_V: float
        :param display_I: Current range to display on 4156C
        :type display_I: float
        :param comp_I: a
        :type comp_I: float
        :return: Vs, Is, aborted. Debug mode: returns [0,0.001,0.002,0.001,0], [0,1e-6,2e-6,1e-6,0], False
        :rtype: (list of float, list of float, bool)
        """
        if display_I <= 0:
            raise ValueError()
        if math.copysign(1, end_V) != math.copysign(1, step_V):
            print('Warning: using step_V {} instead of {}.'.format(-step_V, step_V))
            step_V = -step_V
        number_of_step = end_V/step_V
        if number_of_step > 1001:
            raise RuntimeError('Number of step exceeds 1001. (see the manual of 4156C)')
        if self._debug_mode:
            return [0,0.001,0.002,0.001,0], [0,1e-6,2e-6,1e-6,0], False
        is_P = end_V > 0  # is positive sweep
        self.w('*RST')
        query_resp = self.q('SYST:ERR?')
        if query_resp != '+0,"No error"\n':
            raise RuntimeError('Agilent 4156C error: {}'.format(query_resp))
        self.disable_all_units(gnd_smu, swp_smu)
        self.configure_smu(gnd_smu, 3, 3)
        self.configure_smu(swp_smu, 1, 1)
        if self._use_us_commands:
            raise NotImplementedError
        else:
            self.w(":PAGE:MEAS:VAR1:MODE DOUB;")
            self.w(":PAGE:MEAS:SWE:VAR1:STAR 0")
            self.w(":PAGE:MEAS:VAR1:STOP {};".format(end_V))
            self.w(":PAGE:MEAS:VAR1:STEP {};".format(step_V))
            # TODO: hold time, deley time
            # TODO: stop at abnormal
        self.set_Y2("I{}".format(swp_smu), True)
        self.configure_display(0 if is_P else end_V,
                               end_V if is_P else 0,
                               0 if is_P else -display_I,
                               display_I if is_P else 0,
                               1e-15 if is_P else -10e-3,
                               10e-3 if is_P else -1e-15)
        self.w(':PAGE:SCON:MEAS:SING')
        self.q('*OPC?')
        Vs = [float(V) for V in self.q(":FORM:DATA ASC;:DATA? 'V{}';".format(swp_smu)).split(',')]
        Is = [float(I) for I in self.q(":FORM:DATA ASC;:DATA? 'I{}';".format(swp_smu)).split(',')]
        Vs = [V for V in Vs if V != 9.91e307]
        aborted = len(Vs) != len(Is)
        Is = [I for I in Is if I != 9.91e307]
        if len(Vs) != len(Is):
            raise Exception
        return Vs, Is, aborted
