from instr.base import TemperatureController


class Sci9700(TemperatureController):
    """ Scientific Instruments Model 9700"""
    def __init__(self, rsrc=None, timeout_sec=5, reset=True):
        idn = 'Scientific Instruments,9700'
        self._channel = 'A'
        super().__init__(rsrc, idn, timeout_sec, reset)

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value):
        if value not in ['A', 'B']:
            raise ValueError
        self._channel = value

    def read_heater(self):
        if self._debug_mode:
            return 1234.56789
        else:
            tmp = self.q('HTR?').split()
            return float(tmp[1])

    def read_system_status(self):
        """
        Set point temp, heater, controlmode, heater alarm status, control type,
        zone number
        """
        if self._debug_mode:
            return 'STA 020.000,00.00,1,0,1,1,2'
        else:
            tmp = self.q('STA?')
            return tmp

    def read_temp(self):
        if self._debug_mode:
            return 1234.56789
        else:
            tmp = self.q('T{}?'.format(self.channel)).split()
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
    import visa

    rm = visa.ResourceManager()
    sci_rsrc = rm.open_resource('GPIB0::1::INSTR')

    sci = Sci9700(sci_rsrc)
    sci.channel = 'A'
    tmp = sci.read_temp()
    tmp = sci.read_system_status()
    sci.set_temp(200)
