class BaseInstr:
    def __init__(self, instr_resource, timeout_sec, debug_mode):
        self._debug_mode = debug_mode
        if self._debug_mode:
            return
        self._instr_resource = instr_resource
        self._instr_resource.timeout = timeout_sec * 1000  # millisec

    def q(self, query_str):
        if self._debug_mode:
            return ''
        return self._instr_resource.query(query_str)

    def w(self, write_str):
        if self._debug_mode:
            return
        self._instr_resource.write(write_str)
