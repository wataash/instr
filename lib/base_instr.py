import re

class BaseInstr:
    def __init__(self, instr_rsrc, timeout_sec, debug_mode, idn=None):
        """idn: can be a regular expression"""
        self._debug_mode = debug_mode
        self._instr_rsrc = instr_rsrc
        if not self._debug_mode:
            self._instr_rsrc.timeout = timeout_sec * 1000  # millisec
            idn_res = self.q('*IDN?')
            tmp = re.search(idn, idn_res)
            if tmp is None:
                raise RuntimeError('Failed to connect to a instrument.')            

    def q(self, query_str):
        """
        Query.
        Returns '' if debug mode.

        :param query_str:
        :return:
        """
        if self._debug_mode:
            return ''
        return self._instr_rsrc.query(query_str)

    def w(self, write_str):
        """
        Write.
        Do nothing if debug mode.

        :param write_str:
        :return:
        """
        if self._debug_mode:
            return
        self._instr_rsrc.write(write_str)
