from collections import defaultdict
import math

import numpy as np
from scipy.signal import savgol_filter
import statsmodels.api as sm
import unittest2


def calc_coord(X, Y, dX, dY, xm_mesa, ym_mesa, xm_pad, ym_pad) -> list:
    """
    Calculate various coordinates for a device.

    >>> calc_coord(1, 1, 1000, 1000, 0, 0, 0, 0)
    [1.0, 1.0, 1.0, 1.0]

    >>> calc_coord(0, 3, 1000, 1000, 500, 700, 500, 500)
    [0.5, 3.5, 0.5, 3.7]

    :return: [X_pad, Y_pad, X_mesa, Y_mesa]
    """
    return [
        X + xm_pad / dX,
        Y + ym_pad / dY,
        X + xm_mesa / dX,
        Y + ym_mesa / dY,
    ]


def fit_R3(VIs):
    """
    fit I = c1 V + c2 V^2 + c3 V^3

    :param VIs:
    :return: c1, c2, c3, R2
    """
    Vs, Is = np.array(VIs).T
    X = np.column_stack((Vs, Vs ** 2, Vs ** 3))
    model = sm.OLS(Is, X)
    results = model.fit()
    c1, c2, c3 = results.params
    R2 = results.rsquared
    return float(c1), float(c2), float(c3), float(R2)


def group_lists(lists, key_index=0):
    """
    >>> group_lists([[1, 1], [1, 2], [1, 3], [2, 1], [2, 2], [2, 3]])
    {1: [(1,), (2,), (3,)], 2: [(1,), (2,), (3,)]}

    >>> group_lists([(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)])
    {1: [(1,), (2,), (3,)], 2: [(1,), (2,), (3,)]}

    >>> group_lists([[1, 'a', 'b'], [2, 'a', 'b'], [2, 'a', 'c']])
    {1: [('a', 'b')], 2: [('a', 'b'), ('a', 'c')]}

    >>> group_lists([[1, 'a', 'b'], [2, 'a', 'b'], [2, 'a', 'c']], 2)
    {'b': [(1, 'a'), (2, 'a')], 'c': [(2, 'a')]}
    """
    ret = defaultdict(list)
    for lis in lists:
        if isinstance(lis, tuple):
            # tuple does not have .pop() method.
            lis = list(lis)
        key = lis[key_index]
        lis.pop(key_index)
        ret[key].append(tuple(lis))
    return dict(ret)


def group_lists_mulkey(lists, *key_indices):
    """
    >>> group_lists_mulkey(
    ...     [[1, 2, 'a', 'b'], [2, 3, 'a', 'b'], [2, 3, 'a', 'c']], 2, 3)
    {('a', 'b'): [(1, 2), (2, 3)], ('a', 'c'): [(2, 3)]}

    >>> group_lists_mulkey(
    ...     [[1, 2, 'a', 'b'], [2, 3, 'a', 'b'], [2, 3, 'a', 'c']], 1, 0)
    {(2, 1): [('a', 'b')], (3, 2): [('a', 'b'), ('a', 'c')]}
    """
    ret = defaultdict(list)
    for lis in lists:
        key = ()
        val = ()
        for key_index in key_indices:
            key += (lis[key_index],)
        for i, v in enumerate(lis):
            if i not in key_indices:
                val += (v,)
        ret[key].append(val)
    return dict(ret)


def group_pairs(pairs, key_index=0):
    """
    >>> group_pairs([[1, 1], [1, 2], [1, 3], [2, 1], [2, 2], [2, 3]])
    {1: [1, 2, 3], 2: [1, 2, 3]}

    >>> group_pairs([[1, 1], [1, 2], [1, 3], [2, 1], [2, 2], [2, 3]], 1)
    {1: [1, 2], 2: [1, 2], 3: [1, 2]}
    """
    val_index = key_index - 1  # (val_index, key_index) is (0, -1) or (1, 0)
    ret = defaultdict(list)
    for pair in pairs:
        ret[pair[key_index]].append(pair[val_index])
    return dict(ret)


def is_good_RA(t1, r1_inf, r1_sup, t2, r2_inf, r2_sup, t, r):
    """
    >>> is_good_RA(1, 1, 100,
    ...            10, 100, 10000,
    ...            5, 100)
    True
    """
    if r <= 0:
        return False
    r1_inf = math.log(r1_inf)
    r1_sup = math.log(r1_sup)
    r2_inf = math.log(r2_inf)
    r2_sup = math.log(r2_sup)
    r = math.log(r)
    r_inf = r1_inf + ((r2_inf - r1_inf) / (t2 - t1)) * (t - t1)
    r_sup = r1_sup + ((r2_sup - r1_sup) / (t2 - t1)) * (t - t1)
    return r_inf <= r <= r_sup


def list_to_monolists(lis, key=lambda x: x):
    """
    Convert list to
    list of (monotonic increasing or decreasing list with regular intervals)

    >>> L = [1, 2, 3, 4, 6, 8, 10]
    >>> list_to_monolists(L)
    ... # doctest: +NORMALIZE_WHITESPACE
    ([[1, 2, 3, 4], [6, 8, 10]], [1, 2])

    >>> arr = np.array([(1, -1), (2, 0), (3, 0), (4, 1), (5, 0)])
    >>> list_to_monolists(arr, key=lambda x: x[1])
    ... # doctest: +NORMALIZE_WHITESPACE
    ([[array([ 1, -1]), array([2, 0])],
      [array([3, 0]), array([4, 1])],
      [array([5, 0])]],
     [1, 1, None])

    >>> L = [((1, 1), 'a'), ((4, 2), 'b'), ((9, 2), 'c'), ((16, 1), 'd')]
    >>> list_to_monolists(L, key=lambda x: x[0][1])
    ... # doctest: +NORMALIZE_WHITESPACE
    ([[((1, 1), 'a'), ((4, 2), 'b')],
      [((9, 2), 'c'), ((16, 1), 'd')]],
     [1, -1])
    """
    monolists = []
    diffs = []
    monolist = [lis[0]]
    key_prev = key(lis[0])
    key_diff_prev = None
    for item in lis[1:]:
        key_diff = key(item) - key_prev
        # Using short-circuit evaluation
        if key_diff_prev is None or math.isclose(key_diff, key_diff_prev):
            monolist.append(item)
            key_diff_prev = key_diff
        else:
            monolists.append(monolist)
            diffs.append(key_diff_prev)
            monolist = [item]  # new list
            key_diff_prev = None
        key_prev = key(item)
    monolists.append(monolist)
    diffs.append(key_diff_prev)
    return monolists, diffs


def log_list(start, end, n):
    """
    >>> log_list(1, 100, 7)  #doctest: +NORMALIZE_WHITESPACE
    [1.0, 2.154434690031884, 4.641588833612778, 10.0,
     21.544346900318832, 46.4158883361278, 100.0]

    >>> log_list(-1, -10, 11)  #doctest: +NORMALIZE_WHITESPACE
    [-1.0,  -1.2589254117941673,  -1.5848931924611136,  -1.9952623149688795,
     -2.51188643150958,  -3.1622776601683795,  -3.9810717055349722,
     -5.011872336272722,  -6.309573444801933,  -7.943282347242816,  -10.0]

    >>> log_list(10, 1, 3)
    [10.0, 3.1622776601683795, 1.0]

    >>> log_list(0, 10, 10)
    Traceback (most recent call last):
        ...
    ValueError: start or end cannot be 0.

    >>> log_list(-12.3, 34.1, 21)
    Traceback (most recent call last):
        ...
    ValueError: start and end must have same sign.

    :param start:
    :param end:
    :param n:
    :return:
    """
    if start == 0 or end == 0:
        raise ValueError('start or end cannot be 0.')
    if start < 0 < end or start > 0 > end:
        raise ValueError('start and end must have same sign.')
    if type(n) is not int:
        raise ValueError('steps should be int.')
    return [start * (end / start) ** (i / (n - 1)) for i in range(n)]


def log_list_deprecated(start, end, steps):
    """
    Use log_list instead.
    """
    return log_list(start, end, steps + 1)


def num_9th(value):
    """
    >>> num_9th(0)
    9.64327466553287e-17

    >>> num_9th(0.9)
    0.9999999999999991

    >>> num_9th(0.99)
    1.99999999999999

    >>> num_9th(0.999999)
    5.999999999891079

    >>> num_9th(0.9999999999999999999999999999)
    15.653559774527022

    >>> num_9th(1)
    15.653559774527022

    """
    if not 0 <= value <= 1:
        raise ValueError
    eps = 7. / 3 - 4. / 3 - 1
    return abs(math.log10(1 + eps - value))


def rotate_vector(x, y, theta_deg):
    theta_rad = theta_deg * math.pi / 180
    return math.cos(theta_rad) * x - math.sin(theta_rad) * y, math.sin(
            theta_rad) * x + math.cos(theta_rad) * y


def spiral_XYs(min_X, max_X, min_Y, max_Y):
    """
    >>> spiral_XYs(1, 3, 1, 3)
    [(2, 2), (2, 3), (1, 3), (1, 2), (1, 1), (2, 1), (3, 1), (3, 2), (3, 3)]

    >>> spiral_XYs(1, 2, 1, 2)
    [(1, 2), (1, 1), (2, 1), (2, 2)]

    >>> spiral_XYs(1, 1, 1, 1)
    [(1, 1)]

    >>> spiral_XYs(1, 4, 1, 1)
    [(1, 1), (2, 1), (3, 1), (4, 1)]

    >>> spiral_XYs(1, 1, 1, 3)
    [(1, 1), (1, 2), (1, 3)]

    """
    from itertools import product
    if (min_X > max_X) or (min_Y > max_Y):
        raise ValueError
    XYs = list(product(range(min_X, max_X + 1), range(min_Y, max_Y + 1)))
    res_reverse = []
    while XYs:
        # Go down right side
        app = [(X, Y) for X, Y in XYs if X == max_X and min_Y <= Y <= max_Y]
        XYs = [(X, Y) for X, Y in XYs if not (X, Y) in app]
        app = sorted(app, key=lambda x: x[1], reverse=True)
        res_reverse += app
        max_X -= 1

        # Go left lower side
        app = [(X, Y) for X, Y in XYs if Y == min_Y and min_X <= X <= max_X]
        XYs = [(X, Y) for X, Y in XYs if not (X, Y) in app]
        app = sorted(app, key=lambda x: x[0], reverse=True)
        res_reverse += app
        min_Y += 1

        # Go up left side
        app = [(X, Y) for X, Y in XYs if X == min_X and min_Y <= Y <= max_Y]
        XYs = [(X, Y) for X, Y in XYs if not (X, Y) in app]
        app = sorted(app, key=lambda x: x[1])
        res_reverse += app
        min_X += 1

        # Go right upper side
        app = [(X, Y) for X, Y in XYs if Y == max_Y and min_X <= X <= max_X]
        XYs = [(X, Y) for X, Y in XYs if not (X, Y) in app]
        app = sorted(app, key=lambda x: x[0])
        res_reverse += app
        max_Y -= 1

    res = list(reversed(res_reverse))
    return res


def vis_variance(vis, remove_v=(-20e-3, 20e-3)):
    """
    >>> vis = [(0, 0), (1, 1), (2, 3), (1, 2), (0, 0)]
    >>> vis_variance(vis)
    0.083333333333333329

    >>> vs = np.concatenate((np.linspace(0, 1, 101), np.linspace(1, 0, 101)))

    >>> np.random.seed(0)
    >>> Is = vs + np.random.normal(0, 0.1, 202)
    >>> vis = np.stack((vs, Is), axis=-1)
    >>> vis_variance(vis)
    0.018006625498031975

    >>> vis[:, 1] *= 10
    >>> vis_variance(vis)
    0.018006625498031979

    >>> np.random.seed(0)
    >>> vis[:, 1] = vs + np.random.normal(0, 1, 202)
    >>> vis_variance(vis)
    0.049144157482165544
    """
    if not isinstance(vis, np.ndarray):
        vis = np.array(vis, dtype=np.float64)
    filt = np.bitwise_or(vis[:,0] <= remove_v[0], vis[:,0] >= remove_v[1])
    vis = vis[filt]
    # Normalize
    iave = vis[:, 1].mean()
    vis[:, 1] /= iave
    dic_v_Is = group_pairs(vis.tolist())
    varnorms = []
    for v, Is in dic_v_Is.items():
        if v == 0 or len(Is) == 1:
            continue
        varnorms.append(np.var(Is)/np.average(Is))
    ret = np.average(varnorms)
    return ret


def zigzag_XY(start_X, start_Y, max_X, max_Y, direction='r'):
    """
    X and Y must be grater than or equal to 0.

    Go right, up, left and left
    >>> zigzag_XY(2, 2, 3, 3, 'r')
    [(2, 2), (3, 2), (3, 3), (2, 3), (1, 3)]

    Go left, up and right
    >>> zigzag_XY(2, 1, 2, 2, 'Left')
    [(2, 1), (1, 1), (1, 2), (2, 2)]

    >>> zigzag_XY(2, 2, 3, 3, 'r')
    [(2, 2), (3, 2), (3, 3), (2, 3), (1, 3)]

    >>> zigzag_XY(2, 1, 2, 2, 'Left')
    [(2, 1), (1, 1), (1, 2), (2, 2)]

    >>> zigzag_XY(3, -1, 4, 4)
    Traceback (most recent call last):
        ...
    ValueError: XY out of range.

    >>> zigzag_XY(-1, 3, 4, 4, True)
    Traceback (most recent call last):
        ...
    ValueError: XY out of range.

    >>> zigzag_XY(1, 5, 2, 2)
    Traceback (most recent call last):
        ...
    ValueError: XY out of range.

    :type start_X: int
    :type start_Y: int
    :type max_X: int
    :type max_Y: int
    :rtype: list(tuple(int))
    """
    res = []
    X = start_X
    Y = start_Y

    if start_X < 0 or max_X < start_X or start_Y < 0 or max_Y < start_Y:
        raise ValueError('XY out of range.')

    if direction in ['r', 'right', 'R', 'Right']:
        while X <= max_X:
            res.append((X, Y))
            X += 1
        go_right = False
    elif direction in ['l', 'left', 'L', 'Left']:
        while 1 <= X:
            res.append((X, Y))
            X -= 1
        go_right = True
    else:
        raise ValueError('Wrong direction')  # TODO detailed
    Y += 1

    while Y <= max_Y:
        if go_right:
            res += [(XX, Y) for XX in range(1, max_X + 1)]
            go_right = False
        else:
            res += [(XX, Y) for XX in reversed(range(1, max_X + 1))]
            go_right = True
        Y += 1
    return res


# Depends above ----------------------------------------------------------------
def list_to_monolists_concat(lis, key=lambda x: x):
    """
    list_to_monolists and concatenates at stationary key.
    >>> pairs = [(0, 0), (1, 1),
    ...          (1, 2), (0, 3), (0, 4), (-1, 5),
    ...          (-1, 6), (0, 7),
    ...          (0, 8), (10, 9)]
    >>> list_to_monolists(pairs, key=lambda x: x[0])
    ... # doctest: +NORMALIZE_WHITESPACE
    ([[(0, 0), (1, 1)],
      [(1, 2), (0, 3)],
      [(0, 4), (-1, 5)],
      [(-1, 6), (0, 7)],
      [(0, 8), (10, 9)]],
     [1, -1, -1, 1, 10])

    >>> list_to_monolists_concat(pairs, key=lambda x: x[0])
    ... # doctest: +NORMALIZE_WHITESPACE
    ([[(0, 0), (1, 1)],
      [(1, 2), (0, 3), (-1, 5)],
      [(-1, 6), (0, 7)],
      [(0, 8), (10, 9)]],
      [1, -1, 1, 10])
    """
    lists, diffs = list_to_monolists(lis, key)
    for i in range(len(diffs) - 2, -1, -1):  # Second from last --> 0
        key1 = key(lists[i][-1])
        key2 = key(lists[i + 1][0])
        if math.isclose(diffs[i], diffs[i + 1]) and math.isclose(key1, key2):
            del diffs[i + 1]
            del lists[i + 1][0]
            lists[i] += lists[i + 1]
            del lists[i + 1]
    return lists, diffs


# Depends above ----------------------------------------------------------------
def savgol_vis(vis, window_length, polyoder, deriv=0):
    """
    See test cases.
    """
    ret = []
    viss, dvs = list_to_monolists_concat(vis, key=lambda x: x[0])

    for viss, dv in zip(viss, dvs):
        if len(viss) < window_length:
            print('Skipping in savgol_VIs. (len(viss) < window_length)')
            continue
        Vs, Is = zip(*viss)
        Is = savgol_filter(Is, window_length, polyoder, deriv, dv)
        ret += zip(Vs, Is)
    return ret


class TestAlgorithms(unittest2.TestCase):
    def test_savgol_VIs(self):
        from matplotlib import pyplot as plt
        step = 0.050
        noise = 0.001
        Vs = np.arange(-1, 1.0001, step)
        Vs = np.append(Vs, np.arange(1, -1.0001, -step))
        Vs = np.append(Vs, np.arange(-1, 1.0001, step))
        Is = 0.01 * Vs + np.random.normal(0, noise, len(Vs))

        VIs_raw = list(zip(Vs, Is))
        VIs_10 = savgol_vis(VIs_raw, 1, 0)  # raw
        VIs_50 = savgol_vis(VIs_raw, 5, 0)
        VIs_53 = savgol_vis(VIs_raw, 5, 3)
        VIs_93 = savgol_vis(VIs_raw, 9, 3)

        dVdI_31 = savgol_vis(VIs_raw, 3, 1, 1)
        dVdI_53 = savgol_vis(VIs_raw, 5, 3, 1)
        dVdI_93 = savgol_vis(VIs_raw, 9, 3, 1)
        dVdI_213 = savgol_vis(VIs_raw, 21, 3, 1)

        ddVdI2_32 = savgol_vis(VIs_raw, 3, 2, 2)
        ddVdI3_53 = savgol_vis(VIs_raw, 5, 3, 2)
        ddVdI3_93 = savgol_vis(VIs_raw, 9, 3, 2)
        ddVdI3_213 = savgol_vis(VIs_raw, 21, 3, 2)

        plt.subplot(1, 3, 1)
        plt.plot(*(zip(*VIs_raw)), '.-')
        # plt.plot(*(zip(*VIs_10)), '.-')  # raw
        plt.plot(*(zip(*VIs_50)), '.-')
        plt.plot(*(zip(*VIs_53)), '.-')
        plt.plot(*(zip(*VIs_93)), '.-')

        plt.subplot(1, 3, 2)
        plt.plot(*(zip(*dVdI_31)), '.-')
        plt.plot(*(zip(*dVdI_53)), '.-')
        plt.plot(*(zip(*dVdI_93)), '.-')
        plt.plot(*(zip(*dVdI_213)), '.-')

        plt.subplot(1, 3, 3)
        plt.plot(*(zip(*ddVdI2_32)), '.-')
        plt.plot(*(zip(*ddVdI3_53)), '.-')
        plt.plot(*(zip(*ddVdI3_93)), '.-')
        plt.plot(*(zip(*ddVdI3_213)), '.-')

        plt.show()


if __name__ == '__main__':
    import doctest
    doctest.testmod()
