import math
from operator import itemgetter


def zigzag_XY(start_X, start_Y, max_X, max_Y, go_right_first=True):
    """
    zigzag_XY(2, 2, 3, 3) -> [(2,2), (3,2), (3,3), (2,3), (1,3)] (go right up left left)

    zigzag_XY(2, 1, 2, 2, False) -> [(2,1), (1,1), (1,2), (2,2)] (go left up right)

    :type start_X: int
    :type start_Y: int
    :type max_X: int
    :type max_Y: int
    :type go_right_first: bool
    :rtype: list(tuple(int))
    """
    res = []
    X = start_X
    Y = start_Y

    if start_X < 0 or max_X < start_X or start_Y < 0 or max_Y < start_Y:
        raise ValueError('XY out of range.')

    if go_right_first:
        while X <= max_X:
            res.append((X, Y))
            X += 1
        go_right = False
    else:
        while 1 <= X:
            res.append((X, Y))
            X -= 1
        go_right = True
    Y+= 1

    while Y <= max_Y:
        if go_right:
            res += [(XX, Y) for XX in range(1, max_X + 1)]
            go_right = False
        else:
            res += [(XX, Y) for XX in reversed(range(1, max_X + 1))]
            go_right = True
        Y+= 1
    return res


def ave_xyz(lists):
    """
    # in
    # [[x0, x1, ...],
    #  [y0, y1, ...],
    #  [z0, z1, ...],
    # ...
    # ]
    # [[0, 1, 2, 1, 2],
    #  [1, 2, 3, 4, 5],
    #  [0, 1, 2, 3, 4],
    #  [10, 11, 12, 13, 14]
    # ]
    # out
    # [(0, 1, 2),
    #  (1, 3, 4),
    #  (0, 2, 3),
    #  (10, 12, 13)
    # ]
    :param lists:
    :return:
    """
    xyzs = [xyz for xyz in zip(*lists)]
    xyzs_sorted = sorted(xyzs, key=itemgetter(0))
    res_lists_transposed = []  # [[x0, y0, z0], ... ]
    num_variables = len(xyzs[0])
    prev_x = -999999999
    num_x = 0
    sum_yz = [0] * (num_variables - 1)
    for xyz in xyzs_sorted:
        if xyz[0] != prev_x and num_x != 0:
            res_lists_transposed.append([prev_x] + [y/num_x for y in sum_yz])  # y: y or z or ...
            num_x = 0
            sum_yz = [0] * (num_variables - 1)
        for i, y in enumerate(xyz[1:]):  # y: y or z or ...
            sum_yz[i] += y
        prev_x = xyz[0]
        num_x += 1
    res_lists_transposed.append([prev_x] + [y/num_x for y in sum_yz])  # last x
    return list(zip(*res_lists_transposed))


def rotate_vector(x, y, theta_deg):
    theta_rad = theta_deg * math.pi/180
    return math.cos(theta_rad)*x - math.sin(theta_rad)*y, math.sin(theta_rad)*x + math.cos(theta_rad)*y


if __name__ == '__main__':
    print(zigzag_XY(2, 2, 3, 3))
    print(zigzag_XY(2, 1, 2, 2, False))
    # print(zigzag_XY(3, -1, 4, 4))
    # print(zigzag_XY(-1, 4, 4, 4, True))
    # print(zigzag_XY(1, 5, 2, 2))

    ave = ave_xyz([
        [0, 1, 2, 1, 2],
        [1, 2, 3, 4, 5],
        [0, 1, 2, 3, 4],
        [10, 11, 12, 13, 14]
    ])
    print(ave)
