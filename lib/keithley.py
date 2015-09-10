if __name__ == "__main__" and __package__ is None:
    import visa
    from base_instr import BaseInstr
else:
    from lib.base_instr import BaseInstr


class Keithley2400(BaseInstr):
    """
    Keithley 2400

    Issue: Output remains 'ON' if self._switch_output('OFF') is not called explicitly.
    def __del__(self): self._switch_output('OFF')
    doesn't work.
    """
    def __init__(self, instr_rsrc, timeout_sec, debug_mode=False):
        self._debug_mode = debug_mode
        super().__init__(instr_rsrc, timeout_sec, self._debug_mode, 'KEITHLEY INSTRUMENTS.*24')  # TODO: test
        self.w('reset()')
        self.default_setup()
        self.check_err()


    def _check_err(self):
        if self._debug_mode:
            pass
        else:
            tmp = self.q(':SYST:ERR?')
            if tmp != '0,"No error"\n':
                raise RuntimeError('Error on Keithley 2400.')

    def _configure_src_voltage(self, volt, compliance_current=1e-6):
        if self._debug_mode:
            pass
        else:
            self.w('SOUR:FUNC VOLT;:SOUR:VOLT {};:CURR:PROT {};'.format(volt, compliance_current))
        self.check_err()

    def _default_setup(self):
        """
        From LabVIEW driver
        *ESE 1 - enables OPC reporting
        *SRE 32 -enables standard event bits for OPC reporting
        *CLS - clears status
        FUNC:CONC ON - Enables concurrent measurements
        FUNC:ALL - enables all function readings
        TRAC:FEED:CONT:NEV - disables data buffer
        FORM:SRE - switches data transfer to binary for speed - GPIB only
        RES:MODE MAN - disables auto resistance
        """
        if self._debug_mode:
            pass
        else:
            self.w('*ESE 1;*SRE 32;*CLS;:FUNC:CONC ON;:FUNC:ALL;:TRAC:FEED:CONT NEV;:RES:MODE MAN;')
            self._switch_output('OFF')

    def _switch_output(self, on_off='OFF'):
        """on_off: 'ON' or 'OFF'"""
        if self._debug_mode:
            pass
        else:
            self.w('OUTP {}'.format(on_off))
        self.check_err()


class Keithley2636A(BaseInstr):
    """
    Keithley 2636A
    """
    def __init__(self, instr_rsrc, timeout_sec, debug_mode=False):
        self._debug_mode = debug_mode
        super().__init__(instr_rsrc, timeout_sec, self._debug_mode, 'Keithley Instruments Inc., Model 2636A')
        self._default_setup()

    def _check_err(self):
        tmp = self.q('print(errorqueue.next())')
        if tmp != '0.00000e+00\tQueue Is Empty\t0.00000e+00\n':
            raise RuntimeError('Error on Keithley 2636A.')

    def _configure_src(self, channel='A', src='V', level=0.0, limit=1e-6):
        """
        channel: 'A' or 'B'
        src: 'V' or 'I'
        """
        if channel == 'A':
            smu = 'smua'
        elif channel == 'B':
            smu = 'smub'
        else:
            raise ValueError("channel: 'A' or 'B'")

        if src == 'V':
            out = 'OUTPUT_DCVOLTS'
            src_vi = 'v'
            limit_vi = 'i'
        elif src == 'I':
            out = 'OUTPUT_DCAMPS'
            i = 'i'
            limit_vi = 'v'
        else:
            raise ValueError("src: 'V' or 'I'")

        if level is not float:
            raise ValueError('level: float')
        if limit is not float:
            raise ValueError('limit: float')

        self.w('localnode.{0}.source.func = {0}.{1}'.format(smu, out))  #####
        self.w('localnode.{}.source.level{} = {}'.format(smu, src_vi, level))
        self.w('localnode.{}.source.limit{} = {}'.format(smu, limit_vi, limit))
        self._check_err()

    def _default_setup(self):
        """
        From LabVIEW driver
        """
        self.w('errorqueue.clear() localnode.prompts = 0 localnode.showerrors = 0')
        self._check_err()

    def _output(self, on_off=0):
        """on_off: 0 off, 1 on"""
        self.w('localnode.smua.source.output = '.format(on_off))
        self._check_err()

    def _reset_smu(self, SMU='AB'):
        """SMU: 'A' or 'B' or 'AB'"""
        if self._debug_mode:
            pass
        else:
            if 'A' in SMU:
                self.w('localnode.smua.reset()')
            if 'B' in SMU:
                self.w('localnode.smub.reset()')

    def read_single(self, volt, limit_current):
        # test code
        self.read_single_on(volt, limit_current)
        tmp = self.read_single_read()
        self.read_single_off()
        self._check_err
        return tmp

    def read_single_on(self, volt, limit_current):
        # hard code
        self.w('localnode.smua.reset()')
        self.w('localnode.smua.source.func = smua.OUTPUT_DCVOLTS')
        self.w('localnode.smua.source.levelv = {}'.format(volt))
        self.w('localnode.smua.source.limiti = {}'.format(limit_current))
        self.w('localnode.smua.source.output = 1')

    def read_single_read(self):
        tmp = self.q('printnumber(localnode.smua.measure.i())')
        return float(tmp)

    def read_single_off(self):
        self.w('localnode.smua.source.output = 0')


if __name__ == '__main__':
    rm = visa.ResourceManager()
    #ke2400_rsrc = rm.open_resource('GPIB0::25::INSTR')
    #ke2400 = Keithley2400(ke2400_rsrc, 30)
    #ke2400._check_err()
    #ke2400._switch_output('OFF')

    ke2600_rsrc = rm.open_resource('GPIB0::26::INSTR')
    ke2600 = Keithley2636A(ke2600_rsrc, 30)

    for i in range(10):
        current = ke2600.read_single(1e-3, 100e-6)
        ohm = 1e-3/current
        print(current, ohm)

    #ke2600.read_single_on(1e-3, 1e-6)
    #for i in range(10):
    #    print(ke2600.read_single_read())
    #ke2600.read_single_off()
