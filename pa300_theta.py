"""
Obsolute

Coordinates: from home
Up probers!!
"""

# Std libs
import json
import math
import os
import sqlite3
# Non-std libs
import visa
# My libs
import constants as c
from lib.algorithms import rotate_vector
from lib.suss_pa300 import SussPA300


debug_mode = True
conn_params = sqlite3.connect(c.sql_params)
cur_params = conn_params.cursor()

d_X, d_Y, X_min, X_max, Y_min, Y_max = \
    cur_params.execute(
        'SELECT d_X, d_Y, X_min, X_max, Y_min, Y_max FROM samples \
         WHERE sample=?',
         (c.sw_sample,)).fetchone()
delta_X = X_max - X_min
delta_Y = Y_max - Y_min

rm = visa.ResourceManager()
print(rm.list_resources())
if debug_mode:
    suss = SussPA300(None, c.visa_timeout_sec_suss, debug_mode)
else:
    suss_rsrc = rm.open_resource(c.visa_rsrc_name_suss)
    suss = SussPA300(suss_rsrc, c.visa_timeout_sec_suss, debug_mode)

suss.velocity = 25
suss.separate()
suss.velocity = 5
suss.align()
suss.velocity = 1
input('Right click X{} Y{} and set as home.'.format(X_min, Y_min))
suss.move_to_xy_from_home(- delta_X * d_X, - delta_Y * d_Y)
input('Right click X{} Y{}, press enter.'.format(X_max, Y_max))
(x99_tilled, y99_tilled, _) = suss.read_xyz('H')

theta_diagonal_true = math.atan(delta_Y*d_Y / delta_X*d_X) * 180 / math.pi
theta_diagonal_tilled = math.atan(y99_tilled / x99_tilled) * 180 / math.pi
theta_pattern_tilled = theta_diagonal_tilled - theta_pattern_true
(x11, y11) = rotate_vector(x11_tilled, y11_tilled, -theta_pattern_tilled)  # -409.42796355219554, -421.4851630383946
x00 = x11 + d_X  # 890.5720364478045
y00 = y11 + d_X  # 878.5148369616054
s_x00 = -x00
s_y00 = -y00

print('theta_diagonal: {}'.format(theta_diagonal, s_x00, s_y00))
input('Done.')
