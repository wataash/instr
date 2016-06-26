import math

import unittest2

from instr.base import BaseInstr

"""
Unit of length: um
Coordinate mode
'H': relative to home, 'Z': relative to zero, 'C': relative to center
's': substrate
"""


class SussPA300(BaseInstr):
    def __init__(self, rsrc=None, timeout_sec=15, reset=True):
        idn = 'Suss MicroTec Test Systems GmbH,ProberBench PC,0,0'
        # 30,000um = 3cm
        self._xyz_center_limit_min = (-30000, -30000, 5200)
        self._xyz_center_limit_max = (30000, 30000, 13000)
        self._z_contact = 12000
        self._z_align = self._z_contact - 100
        self._z_separate = self._z_contact - 300
        self._safe_move_separate_threshold_distance = 3000
        super().__init__(rsrc, idn, timeout_sec, reset)
        if self._debug_mode:
            # self._xy_home_deprecated = (0.0, 0.0)
            self._x_home_debug = 0.0
            self._y_home_debug = 0.0
            self._xy_offset_from_home = {'H': (-9669.5, -2349.5),
                                         'C': (0.0, 0.0),
                                         'Z': (157600.0, 155000.0)}
            self._z_debug = 11000.0

    def check_error(self):
        if self._debug_mode:
            super().check_error()
            return
        # Response example: '0: PA300PS_ 5 1 1 1 0 0 0 0 0'
        stat = self.q('ReadSystemStatus')
        if stat.split(':')[0] != '0':
            raise RuntimeError('Error in SUSS. (non-zero status code)')
        x, y, z = self.read_xyz('C')
        if self._exceeds_limit('C', x, y, z):
            raise RuntimeError('Over xyz limit.')

    def reset(self):
        if self._debug_mode:
            super().reset()
            return
        pass
        self.check_error()

    @staticmethod
    def _is_valid_coordinate_mode(coordinate_mode) -> bool:
        """
        >>> suss._is_valid_coordinate_mode('H')
        True

        >>> suss._is_valid_coordinate_mode('C')
        True

        >>> suss._is_valid_coordinate_mode('Z')
        True

        >>> suss._is_valid_coordinate_mode('invalid coord')
        ... # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        ValueError

        :param coordinate_mode: 'H', 'C' or 'Z'
        :return: True
        """
        if coordinate_mode not in ('H', 'Z', 'C'):
            raise ValueError(
                    "Coordinate mode must be one of ('H', 'Z', 'C')"
                    "(relative to home, zero, center, substrate)")
        return True

    def read_xyz(self, coordinate) -> (float, float, float):
        """
        >>> suss.read_xyz('H')
        (-9669.5, -2349.5, 11000.0)

        >>> suss.read_xyz('C')
        (0.0, 0.0, 11000.0)

        >>> suss.read_xyz('invalid coord')  #doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        ValueError

        :type coordinate: string
        :return: [x, y, z] in micrometer.
        """
        self._is_valid_coordinate_mode(coordinate)

        if self._debug_mode:
            x, y = map(sum, zip([self._x_home_debug, self._y_home_debug],
                                self._xy_offset_from_home[coordinate]))
            return x, y, self._z_debug

        # Y: micron.
        res = self.q('ReadChuckPosition Y {} D'.format(coordinate)).split()
        # "0: 0.0 -0.5 -300.08" -> ["0:", "0.0", "-0.5", "-300.08"]
        return tuple(map(float, res[1:]))

    @property
    def z(self) -> float:
        z = self.read_xyz('H')[2]
        if self._z_contact - 1 < z < self._z_contact + 1:
            return self._z_contact
        elif self._z_align - 1 < z < self._z_align + 1:
            return self._z_align
        elif self._z_separate - 1 < z < self._z_separate + 1:
            return self._z_separate
        else:
            return z

    def _convert_coord(self, coord_mode_from, coord_mode_to, *xyz):
        """
        >>> suss._convert_coord('H', 'C', 0, 0, 11000)
        (9669.5, 2349.5, 11000.0)

        >>> suss._convert_coord('Z', 'Z', 234, 43, 10000)
        (234, 43, 10000)
        """
        self._is_valid_coordinate_mode(coord_mode_from)
        self._is_valid_coordinate_mode(coord_mode_to)

        if coord_mode_from == coord_mode_to:
            return xyz

        xyz_now_from = self.read_xyz(coord_mode_from)
        xyz_now_to = self.read_xyz(coord_mode_to)
        xyz_offset = [xt - xf for xf, xt in zip(xyz_now_from, xyz_now_to)]
        ret = tuple(map(sum, zip(xyz, xyz_offset)))
        return ret

    def _exceeds_limit(self, coord_mode, *xyz):
        """
        Check (x_center, y_center, y_center) is in limit.

        >>> suss._exceeds_limit('H', 0, 0, 10000)
        False

        # checks only x and y
        >>> suss._exceeds_limit('C', -99999, 99999)
        True

        :param xyz:
        :param coord_mode:
        :return:
        """
        xyz = self._convert_coord(coord_mode, 'C', *xyz)
        for (position, n_lim) in zip(xyz, self._xyz_center_limit_min):
            if position < n_lim:
                return True
        for (position, p_lim) in zip(xyz, self._xyz_center_limit_max):
            if p_lim < position:
                return True
        return False

    def _move_xy(self, coord, velocity, *xy):
        """
        Debug mode: only check_error().
        (Home coord with theta_sample calibrated)
        """
        # TODO implement 'm' mesa coordinate, using self.x_offset (property), y
        # TODO output when debug
        xy = self._convert_coord(coord, 'C', *xy)
        if self._exceeds_limit('C', *xy):
            raise RuntimeError('Exceeds xy limit.')
        if self._debug_mode:
            self._x_home_debug, self._y_home_debug = \
                self._convert_coord('C', 'H', *xy)
            return
        # TODO implement
        # example '7 7 0 0 L 1 C 0'
        # query_response = self.q('ReadChuckStatus')
        # if not separation or alignment
        # if not query_response.split()[6] in ('S', 'A'):
        #     raise RuntimeError('Separate or align before!')
        self.q('MoveChuck {} {} C Y {}'.format(*xy, velocity))
        self.check_error()

    def _move_z(self, velocity, z):
        """
        Debug mode: only checks given z
        velocity 1 -> about 4s/100um
        """
        if not (self._xyz_center_limit_min[2] < z <
                    self._xyz_center_limit_max[2]):
            raise RuntimeError('Parameter exceeds z limit.')
        self.check_error()
        self.q('MoveChuckZ {} Z Y {}'.format(z, velocity))
        self.check_error()

    def approach_separate(self):
        if self.z >= self._z_separate:
            print('Already z >= z_separate.')
            return
        self._move_z(20, self._z_separate)

    def approach_align(self):
        if self.z >= self._z_align:
            print('Already z >= z_align.')
            return
        self.approach_separate()
        self._move_z(5, self._z_align)

    def contact(self):
        """Debug mode: only checks given z"""
        if self.z >= self._z_contact:
            print('Already z >= z_contact.')
            return
        self.approach_align()
        self._move_z(1, self._z_contact)

    def separate_align(self):
        if self.z <= self._z_align:
            print('Already z <= z_align.')
            return
        self._move_z(1, self._z_align)

    def separate_separate(self):
        if self.z <= self._z_separate:
            print('Already z <= z_separate.')
            return
        self._move_z(5, self._z_separate)

    def safe_move(self, coord, x, y):
        x0, y0, _ = self.read_xyz(coord)
        x_move = x - x0
        y_move = y - y0
        distance = math.hypot(x_move, y_move)
        if self._safe_move_separate_threshold_distance < distance:
            self.separate_separate()
            self._move_xy(coord, 20, x, y)
        else:
            self.separate_align()
            self._move_xy(coord, 1, x, y)

    def safe_move_contact(self, coord, x, y):
        self.safe_move(coord, x, y)
        self.contact()


class TestSussPA300(unittest2.TestCase):
    def test00(self):
        suss.check_error()
        suss.reset()

    def test10_move_xy(self):
        suss._move_xy('H', 5, 0, 0)
        suss._move_xy('C', 25, 0, 0)

    def test20_move_z(self):
        suss._move_z(20, 11000)

    def test30_separates(self):
        suss.separate_separate()
        suss.separate_align()
        suss.approach_separate()
        suss.approach_align()
        suss.contact()
        suss.approach_align()
        suss.approach_separate()
        suss.separate_align()
        suss.separate_separate()

    def test40_safe_move(self):
        suss.contact()
        suss.safe_move('H', 0, 0)
        suss.safe_move('H', -100, -100)
        suss.safe_move('H', -2000, -2000)
        suss.safe_move_contact('H', 0, 0)


if __name__ == '__main__':
    import doctest

    debug_mode = False

    if debug_mode:
        suss_rsrc = None
    else:
        import visa

        rm = visa.ResourceManager()
        print(rm.list_resources())
        suss_rsrc = rm.open_resource('GPIB0::7::INSTR')
        suss_rsrc.timeout = 15
    suss = SussPA300(rsrc=suss_rsrc)

    doctest.testmod(extraglobs={'suss': suss})

    if not debug_mode:
        resp = input('Use debugger! Doing dengerous test.')
        if resp != 'yes':
            raise RuntimeError('Use debugger and execute lines one-by-one.')
    unittest2.main()
