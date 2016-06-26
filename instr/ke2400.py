from instr.base import SourceMeter


"""
Keithley 2400

Issue: Output remains 'ON' if self._switch_output('OFF') is not called
explicitly.
def __del__(self): self._switch_output('OFF')
doesn't work.
"""


class Keithley2400(SourceMeter):
    def __init__(self, **kwargs):
        super().__init__(idn='KEITHLEY INSTRUMENTS.*24', **kwargs)
        self.reset()

    def check_error(self):
        if self._debug_mode:
            self._dbg_print_skip_method()
            return
        else:
            resp = self.q(':SYST:ERR?')
            if resp != '0,"No error"\n':
                raise RuntimeError('Error on Keithley 2400.')

    def reset(self):
        if self._debug_mode:
            self._dbg_print_skip_method()
            return
        self.w('reset()')
        self.check_error()

    def iv_sweep(self, v_start, v_end, v_step=1e-3, v_points=None,
                 i_limit=1e-3):
        self.reset()
        self.w(':SENS:FUNC:CONC OFF')
        self.w(':SENS:CURR:PROT {}'.format(i_limit))  # TODO: format
        self.w(':SOUR:VOLT:START {}'.format(v_start))
        self.w(':SOUR:VOLT:STOP {}'.format(v_end))

        self.w('')
        self.w('OUTPUT ON')
        resp = self.q(':READ?')

if __name__ == '__main__':
    import visa

    rm = visa.ResourceManager()
    ke24_rsrc = rm.open_resource('GPIB0::27::INSTR')
    ke24 = Keithley2400(debug_mode=False, instr_rsrc=ke24_rsrc)
    ke24.iv_sweep(0, 0.1)
