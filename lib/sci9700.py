if __name__ == "__main__" and __package__ is None:
    import visa
    from base_instr import BaseInstr
else:
    from lib.base_instr import BaseInstr


class Sci9700(BaseInstr):
    """ Scientific Instruments Model 9700"""
    def __init__(self, instr_rsrc, timeout_sec, debug_mode=False):
        self._debug_mode = debug_mode
        super().__init__(instr_rsrc, timeout_sec, self._debug_mode, 'Scientific Instruments,9700')  # TODO: test


    def read_heater(self):
        if self._debug_mode:
            return 1234.56789
        else:
            tmp = self.q('HTR?').split()
            return float(tmp[1])

    def read_system_status(self):
        """
        Set point temp, heater, controlmode, heater alarm status, control type, zone number
        """
        if self._debug_mode:
            return 'STA 020.000,00.00,1,0,1,1,2'
        else:
            tmp = self.q('STA?')
            return tmp

    def read_temp(self, channel='A'):
        """
        channel: 'A' or 'B'
        :rtype: float
        """
        if self._debug_mode:
            return 1234.56789
        else:
            tmp = self.q('T{}?'.format(channel)).split()
            return float(tmp[1])

    def set_temp(self, temp):
        """
        :type temp: float
        """
        if self._debug_mode:
            pass
        else:
            self.w('SET {}'.format(temp))


if __name__ == '__main__':
    rm = visa.ResourceManager()
    sci_rsrc = rm.open_resource('GPIB0::1::INSTR')
    sci = Sci9700(sci_rsrc, 3)
    tmp = sci.read_heater()
    tmp = sci.read_system_status()
    tmp = sci.read_temp('A')
    sci.set_temp(200)
