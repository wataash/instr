from lib.base_instr import BaseInstr


class SussPA300(BaseInstr):
    """
    Unit of length: um
    """
    def __init__(self, instr_rsrc, timeout_sec, debug_mode=False):
        self._debug_mode = debug_mode
        super().__init__(instr_rsrc, timeout_sec, self._debug_mode)
        self._negative_xyz_limit_from_center = (-30000, -30000, 5200)  # 20,000um = 2cm
        self._positive_xyz_limit_from_center = (30000, 30000, 13000)
        self._z_contact = 12000
        self._z_align = self._z_contact - 100
        self._z_separate = self._z_contact - 300
        if self._debug_mode:
            return
        if self.q('*IDN?') != 'Suss MicroTec Test Systems GmbH,ProberBench PC,0,0':
            raise RuntimeError('Failed to connect to SUSS PA300.')
        # self.w('*RST')
        self.check_status()
    

    def read_xyz(self, coordinate):
        """
        Returns [x, y, z] in micro meter.
        'H': relative to home,'Z': relative to zero, 'C': relative to center.
        Debug mode: returns [-2424.0, -2425.5, -100.0] for 'H',
        [157599.5, 155000.0, 10947.6] for 'Z' and [-0.5, 0.0, 10947.6] for 'C'

        :type coordinate: string
        :return: [x, y, z]
        """
        if coordinate not in ('H', 'Z', 'C'):
            raise ValueError("Parameter coordinate must be one of ('H', 'Z', 'C')"
                             "(relative to home, zero, center)")
        if self._debug_mode:
            if coordinate == 'H':
                return [-2424.0, -2425.5, -100.0]
            if coordinate == 'Z':
                return [157599.5, 155000.0, 10947.6]
            if coordinate == 'C':
                return [-0.5, 0.0, 10947.6]
        res = self.q('ReadChuckPosition Y {} D'.format(coordinate)).split()  # Y: micron.
        return [float(elem) for elem in res[1:]]  # "0: 0.0 -0.5 -300.08" -> ["0:", "0.0", "-0.5", "-300.08"]

    _velocity = 1

    @property
    def velocity(self):
        return self._velocity

    @velocity.setter
    def velocity(self, value):
        if value <= 0 or 100 < value: raise ValueError('Invalid velocity.')
        self._velocity = value

    def _over_limit_from_center(self, xyz):
        """self._over_limit_from_center((10, 10)) --> checks only x and y"""
        for (position, n_lim) in zip(xyz, self._negative_xyz_limit_from_center):
            if position < n_lim:
                return True
        for (position, p_lim) in zip(xyz, self._positive_xyz_limit_from_center):
            if p_lim < position:
                return True
        return False

    def check_status(self):
        """Do nothing if debug mode."""
        if self._debug_mode:
            return
        stat = self.q('ReadSystemStatus')  # Query example: '0: PA300PS_ 5 1 1 1 0 0 0 0 0'
        if stat.split(':')[0] != '0':
            raise RuntimeError('Something error in SUSS. (non-zero status code)')
        x, y, z = self.read_xyz('C')
        if self._over_limit_from_center((x, y, z)):
            raise RuntimeError('Over xyz limit.')

    def move_to_xy_from_center(self, x, y):
        """Debug mode: only checks x and y."""
        if self._over_limit_from_center((x, y)):
            raise RuntimeError('Exceeds xy limit.')
        if self._debug_mode:
            return
        query_response = self.q('ReadChuckStatus')  # example '7 7 0 0 L 1 C 0'
        # if not separation or alignment # TODO implement
        # if not query_response.split()[6] in ('S', 'A'):
        #     raise RuntimeError('Separate or align before!')
        self.q('MoveChuck {} {} C {}'.format(x, y, self._velocity))
        self.check_status()

    def move_to_xy_from_home(self, x, y):
        """Debug mode: only checks x and y."""
        xy_from_home = self.read_xyz('H')[:2]
        xy_from_center = self.read_xyz('C')[:2]
        self.move_to_xy_from_center(x + xy_from_center[0] - xy_from_home[0], y + xy_from_center[1] - xy_from_home[1])

    def separate(self):
        """Debug mode: only checks given z"""
        self.moveZ(self._z_separate)
        self.check_status()

    def align(self):
        """Debug mode: only checks given z"""
        #self.q('MoveChuckAlignt {}'.format(self.velocity))  # velocity ignored?
        self.moveZ(self._z_align)
        self.check_status()

    def contact(self):
        """Debug mode: only checks given z"""
        #self.q('MoveChuckContact {}'.format(self.velocity))  # velocity ignored?
        self.moveZ(self._z_contact)
        self.check_status()

    def moveZ(self, z):
        """Debug mode: only checks given z"""
        if z < self._negative_xyz_limit_from_center[2] or self._positive_xyz_limit_from_center[2] < z:
            raise RuntimeError('Parameter exceeds z limit.')
        self.q('MoveChuckZ {} Z Y {}'.format(z, self.velocity))
        self.check_status()
