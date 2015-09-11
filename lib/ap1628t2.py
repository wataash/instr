import time

if __name__ == "__main__" and __package__ is None:
    import visa
    from base_instr import BaseInstr
else:
    from lib.base_instr import BaseInstr


class AP1628T2(BaseInstr):
    """Controls Tamagawa electromagnet"""
    def __init__(self, instr_rsrc, timeout_sec, debug_mode=False):
        self._debug_mode = debug_mode
        super().__init__(instr_rsrc, timeout_sec, self._debug_mode, 'TAKASAGO,AP-1628T,00000,Ver2.30Rev1.06\r\n')
        if not debug_mode:
            self.q('*RST')  # Set output zero. TODO: Is it dengerous when 1T->0T ?
            self._analog_value = 0
            self._analog_delta = 10
            self._sleep_sec = 0.001

    def _analog(self, value):
        """
        value: -32000 to 32000
        Use int(value).
        returns int(value).
        """
        rounded_value = int(value)
        if not -32000 <= rounded_value <= 32000:
            raise ValueError('Not -32000 <= value <= 32000 .')
        if self._debug_mode:
            pass
        else:
            while self._analog_value != rounded_value:
                if self._analog_value < rounded_value:
                    self._analog_value += min(abs(self._analog_delta), rounded_value - self._analog_value)
                elif self._analog_value > rounded_value:
                    self._analog_value += max(-abs(self._analog_delta), rounded_value - self._analog_value)
                if not self._debug_mode:
                    tmp = self.q('A1D {}'.format(self._analog_value))
                print('{:>10}/{:<10} {:.3f}/{}G'.format(self._analog_value, value, self._analog_value/3.2, rounded_value/3.2))
                time.sleep(self._sleep_sec)
        return rounded_value
                
        
    def out_tesla(self, tesla):
        """
        tesla: -1T to 1T
        Returns rounded Tesla.
        """
        # TODO: consider hysteresis
        rounded_value = self._analog(tesla * 32000)
        return rounded_value/32000

    def out_gauss(self, gauss):
        """
        gauss: -10000G to 10000G
        Returns rounded Gauss.
        """
        # TODO: consider hysteresis
        rounded_value = self._analog(gauss * 3.2)
        return rounded_value/3.2

    def demagnitize():
        """Remove hysteresis"""
        raise NotImplementedError
    

if __name__ == '__main__':
    rm = visa.ResourceManager()
    ap_rsrc = rm.open_resource('GPIB0::3::INSTR')
    ap = AP1628T2(ap_rsrc, 5)
    tmp = ap.out_gauss(100)
