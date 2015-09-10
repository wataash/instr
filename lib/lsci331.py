if __name__ == "__main__" and __package__ is None:
    import visa
    from base_instr import BaseInstr
else:
    from lib.base_instr import BaseInstr


class LSCI331(BaseInstr):
    """LakeShore 331 Temereture Controller"""
    def __init__(self, instr_rsrc, timeout_sec, debug_mode=False):
        self._debug_mode = debug_mode
        super().__init__(instr_rsrc, timeout_sec, self._debug_mode)
        if not debug_mode:
            if self.q('*IDN?') != 'LSCI,MODEL331S,333342,061404':
                raise RuntimeError('Failed to connect to LCSI 331.')
            self.q('*RST')  # TODO: work?
            self.q('*CLS')  # TODO: work?

    def read_temp_kelvin(self, input_='A', unit='K'):
        """input_ 'A' or 'B'
        unit 'K' Kelvin 'C' degC 'S' sensor
        returns -1111.1 if debug"""
        if not input_ in ['A', 'B']:
            raise ValueError('input_ must be either "A" or "B".')
        if not unit in ['C', 'K', 'S']:
            raise ValueError('unit must be "C", "K" or "S".')
        if self._debug_mode:
            return -1111.1
        else:
            return float(self.q(unit + 'RDG? ' + input_))
            
        

"""
IDN
LSCI,MODEL331S,333342,061404
if MODEL331

LSCI 331 Utility Default Instrument Setup.vi
DFLT 99
This Utility VI sends a default command string to the instrument whenever a new VISA session is opened, or the instrument is reset.  This VI is intended to be used as a subVI for the LSCI 331 Initialize and LSCI 331 Reset VI's.  Altering this VI could cause these two VI's to operate incorrectly.
"""
