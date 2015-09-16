"""
Coordinates: from home
Up probers!!
"""

# Std libs
import json
import math
# Non-std libs
import visa
# My libs
from lib.algorithms import rotate_vector
from lib.suss_pa300 import SussPA300


debug_mode = False
with open('pa300_theta.json') as f:
    j = json.load(f)

rm = visa.ResourceManager()
print(rm.list_resources())
if debug_mode:
    suss = SussPA300(None, j['visa_timeout_sec_suss'], debug_mode)
else:
    suss_rsrc = rm.open_resource(j['visa_rsrc_name_suss'])
    suss = SussPA300(suss_rsrc, j['visa_timeout_sec_suss'], debug_mode)

suss.velocity = 25
suss.separate()
suss.velocity = 5
suss.align()
suss.velocity = 1
input('Right click left down edge, set home, right click X1Y1 and press enter.')
(x11_tilled, y11_tilled, _) = suss.read_xyz('H')  # -415.0, -416.0
suss.move_to_xy_from_home(- j['s_max_X'] * j['s_distance_between_mesa'], 0)
input('Right click X{} Y1, press enter.'.format(j['s_max_X']))
(x91_tilled, y91_tilled, _) = suss.read_xyz('H')  # -13415.5, -243.0
suss.move_to_xy_from_home(- j['s_max_X'] * j['s_distance_between_mesa'], - j['s_max_Y'] * j['s_distance_between_mesa'])
input('Right click substrate top right edge and press enter.')
(xRU_tilled, yRU_tilled, _) = suss.read_xyz('H')  # -13804.5, -5211.5

theta_diagonal_tilled = math.atan(yRU_tilled / xRU_tilled) * 180 / math.pi  # 20.682616056041926
theta_pattern_tilled = math.atan((y91_tilled - y11_tilled) / (x91_tilled - x11_tilled)) * 180 / math.pi  # -0.7624002793812416
theta_diagonal = theta_diagonal_tilled - theta_pattern_tilled  # 21.44501633542317
(x11, y11) = rotate_vector(x11_tilled, y11_tilled, -theta_pattern_tilled)  # -409.42796355219554, -421.4851630383946
x00 = x11 + j['s_distance_between_mesa']  # 890.5720364478045
y00 = y11 + j['s_distance_between_mesa']  # 878.5148369616054
s_x00 = -x00
s_y00 = -y00

print('theta_diagonal: {}'.format(theta_diagonal, s_x00, s_y00))
print('s_x00: {}'.format(s_x00))
print('s_y00: {}'.format(s_y00))
input('Done.')
