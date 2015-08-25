import math
from operator import itemgetter


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

if __name__ == '__main__':
    ave = ave_xyz([
        [0, 1, 2, 1, 2],
        [1, 2, 3, 4, 5],
        [0, 1, 2, 3, 4],
        [10, 11, 12, 13, 14]
    ])
    print(ave)

def rotate_vector(x, y, theta_deg):
    theta_rad = theta_deg * math.pi/180
    return math.cos(theta_rad)*x - math.sin(theta_rad)*y, math.sin(theta_rad)*x + math.cos(theta_rad)*y
