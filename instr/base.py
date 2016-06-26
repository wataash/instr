import inspect
from math import floor
import re

import numpy as np
import visa


class BaseInstr:
    def __init__(self, rsrc, idn=None, timeout_sec=5, reset=True):
        """
        >>> b = BaseInstr(None)
        debug mode (BaseInstr): skip BaseInstr.__init__.

        >>> rm = visa.ResourceManager()
        ... # rm = visa.ResourceManager('C:\\Windows\\system32\\visa32.dll')
        >>> rm.list_resources()

        >>> rsrc = rm.open_resource('visa://169.254.136.196/GPIB0::4::INSTR')
        >>> rsrc.timeout = 60*1000  # 60s
        >>> idn = 'LSCI,MODEL331S,333342,061404'
        >>> b = BaseInstr(rsrc, idn, reset=True)

        :param rsrc: Instrument VISA resource
        :param timeout_sec: second
        :type timeout_sec: int
        :type reset: bool
        :param idn: can be a regular expression.
        :type idn: str
        """
        self._debug_mode = True if rsrc is None else False
        if self._debug_mode:
            self._dbg_print('skip BaseInstr.__init__.')
        else:
            self._rsrc = rsrc
            self._rsrc.timeout = timeout_sec * 1000  # millisec
            resp_idn = self.q('*IDN?')
            match = re.search(idn, resp_idn)
            if match is None:
                raise RuntimeError('Failed to connect to a instrument. '
                                   '*IDN? response: {}'.format(resp_idn))
            if reset:
                self.reset()

    def _dbg_print(self, *objects, sep=' ', end='\n', file=None, flush=False):
        """
        Parameters: same as built-in print() function.

        >>> b = BaseInstr(None)
        debug mode (BaseInstr): skip BaseInstr.__init__.

        >>> b._dbg_print('Hello ', end='World!\\n')
        debug mode (BaseInstr): Hello World!
        """
        if not self._debug_mode:
            raise RuntimeError('Not debug mode.')
        print('debug mode ({}): '.format(self.__class__.__name__), end='')
        print(*objects, sep=sep, end=end, file=file, flush=flush)

    def _dbg_print_skip_method(self):
        """
        >>> b = BaseInstr(None)
        debug mode (BaseInstr): skip BaseInstr.__init__.
        >>> b._dbg_print_skip_method()
        debug mode (BaseInstr): skip <module>.
        >>> b.func = lambda : b._dbg_print_skip_method()
        >>> b.func()
        debug mode (BaseInstr): skip <lambda>.
        """
        stk = inspect.stack()
        self._dbg_print('skip {}.'.format(stk[1][3]))

    def q(self, query_str, chkerr=False):
        """
        VISA query.

        >>> b = BaseInstr(None)
        debug mode (BaseInstr): skip BaseInstr.__init__.

        >>> b.q('*IDN?')
        debug mode (BaseInstr): q: return empty string.
        ''

        :param query_str:
        :param chkerr:
        :return: debug mode -> ''
        :rtype: str
        """

        if self._debug_mode:
            self._dbg_print('q: return empty string.')
            res = ''
        else:
            res = self._rsrc.query(query_str)

        if chkerr:
            self.check_error()
        return res

    def w(self, write_str, chkerr=False):
        """
        Write.
        Do nothing if debug mode.

        >>> b = BaseInstr(None)
        debug mode (BaseInstr): skip BaseInstr.__init__.
        >>> b.w('*RST', True)
        debug mode (BaseInstr): skip w.
        debug mode (BaseInstr): skip check_error.
        """
        if self._debug_mode:
            self._dbg_print_skip_method()
        else:
            self._rsrc.write(write_str)

        if chkerr:
            self.check_error()

    # Abstract methods ---------------------------------------------------------
    def check_error(self):
        """
        Call super if debug mode.

        >>> b = BaseInstr(None)
        debug mode (BaseInstr): skip BaseInstr.__init__.

        >>> b.check_error()
        debug mode (BaseInstr): skip check_error.
        """
        if self._debug_mode:
            self._dbg_print_skip_method()
            return
        else:
            raise NotImplementedError

    def reset(self):
        """
        Call super if debug mode.
        check_error() after reset.
        """
        if self._debug_mode:
            self._dbg_print_skip_method()
            self.check_error()
        else:
            raise NotImplementedError()


class SourceMeter(BaseInstr):
    @staticmethod
    def _v_points_to_step(v_start, v_end, v_points):
        """
        :return: v_step (Always positive value.)
        :rtype: float

        >>> s = SourceMeter(None)
        debug mode (SourceMeter): skip BaseInstr.__init__.
        >>> s._v_points_to_step(0, 1, 11)
        0.1
        >>> s._v_points_to_step(-1, -2, 11)
        0.1
        """
        return abs(v_end - v_start)/(v_points - 1)

    @staticmethod
    def _v_step_to_points(v_start, v_end, v_step):
        """
        >>> s = SourceMeter(None)
        debug mode (SourceMeter): skip BaseInstr.__init__.
        >>> s._v_step_to_points(0, 1, 0.1)
        11
        >>> s._v_step_to_points(0, 1, 0.101)
        10
        >>> s._v_step_to_points(-1, -2, 0.1)
        11

        :param v_step: Must be positive.
        """
        if v_step < 0:
            raise ValueError('v_step must be positive.')
        return floor(abs(v_end - v_start)/v_step) + 1

    # Abstract methods ---------------------------------------------------------
    def iv_sweep(self, v_start, v_end, v_step=1e-3, v_points=None,
                 i_limit=1e-3):
        """
        Call super().iv_sweep if debug mode.
        debug mode: Simulate 1kOhm resistance with noise ~1nA.

        >>> s = SourceMeter(None)
        debug mode (SourceMeter): skip BaseInstr.__init__.

        >>> np.random.seed(1)
        >>> s.iv_sweep(1e-3, 3e-3, 1e-3)  # doctest: +NORMALIZE_WHITESPACE
        debug mode (SourceMeter): iv_sweep: Return dummy data.
        (array([[  1.00000000e-03,   1.00162435e-06],
               [  2.00000000e-03,   2.00162435e-06],
               [  3.00000000e-03,   3.00162435e-06]]), False)

        >>> np.random.seed(1)
        >>> s.iv_sweep(1, -1, 1)  # doctest: +NORMALIZE_WHITESPACE
        debug mode (SourceMeter): iv_sweep: Return dummy data.
        (array([[  1.00000000e+00,   1.00000162e-03],
               [  0.00000000e+00,   1.62434536e-09],
               [ -1.00000000e+00,  -9.99998376e-04]]), False)

        >>> np.random.seed(1)
        >>> s.iv_sweep(0, 1, 2)
        debug mode (SourceMeter): iv_sweep: Return dummy data.
        (array([[  0.00000000e+00,   1.62434536e-09]]), False)

        :param i_limit: positive. (absolute value)
        :type v_start: float
        :type v_end: float
        :type v_step: float
        :param v_points: overrides v_step
        :type v_points: int
        :return: [(v0, i0), (v1, i1), ...], is_aborted
        :rtype: np.ndarray, bool
        """
        if v_points is None:
            v_points = self._v_step_to_points(v_start, v_end, v_step)
        if self._debug_mode:
            self._dbg_print('iv_sweep: Return dummy data.')
            vs = np.linspace(v_start, v_end, v_points)
            Is = vs / 1000 + np.random.normal(0, 1e-9)
            vis = np.array([vs, Is]).transpose()
            return vis, False
        else:
            raise NotImplementedError()

    def iv_sweep_double(self, v_max, v_step=1e-3, v_points=None,
                        i_limit=1e-3):
        """
        Call super if debug mode.
        Sweep 0V -> v_max -> 0V

        >>> s = SourceMeter(None)
        debug mode (SourceMeter): skip BaseInstr.__init__.

        >>> np.random.seed(1)
        >>> s.iv_sweep_double(0.1, 0.1)  # doctest: +NORMALIZE_WHITESPACE
        debug mode (SourceMeter): iv_sweep: Return dummy data.
        debug mode (SourceMeter): iv_sweep: Return dummy data.
        (array([[  0.00000000e+00,   1.62434536e-09],
               [  1.00000000e-01,   1.00001624e-04],
               [  1.00000000e-01,   9.99993882e-05],
               [  0.00000000e+00,  -6.11756414e-10]]), False)

        >>> np.random.seed(1)
        >>> s.iv_sweep_double(0.1, v_points=2)
        debug mode (SourceMeter): iv_sweep: Return dummy data.
        debug mode (SourceMeter): iv_sweep: Return dummy data.
        (array([[  0.00000000e+00,   1.62434536e-09],
               [  1.00000000e-01,   1.00001624e-04],
               [  1.00000000e-01,   9.99993882e-05],
               [  0.00000000e+00,  -6.11756414e-10]]), False)

        :param i_limit: positive. (even if negative sweep)
        :param v_max: can be negative.
        :param v_points: overrides v_step
        :return: [(v0, i0), (v1, i1), ... (v0, i2n)], is_aborted
        :rtype: (np.ndarray, bool)
        """
        # Implementation example
        vis1, aborted = self.iv_sweep(0, v_max, v_step=v_step,
                                      v_points=v_points, i_limit=i_limit)
        if aborted:
            return vis1, aborted
        vis2, aborted = self.iv_sweep(v_max, 0, v_step=v_step,
                                      v_points=v_points, i_limit=i_limit)
        vis = np.concatenate((vis1, vis2))
        return vis, aborted


class TemperatureController(BaseInstr):
    def read_temp(self):
        raise NotImplementedError

if __name__ == '__main__':
    import doctest
    doctest.testmod()
