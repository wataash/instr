import math

import visa

from lib.suss_pa300 import SussPA300


# Coordinates: from home
# Up prober !!!!


def rotate_vector(x, y, theta_deg):
    theta_rad = theta_deg * math.pi/180
    return math.cos(theta_rad)*x - math.sin(theta_rad)*y, math.sin(theta_rad)*x + math.cos(theta_rad)*y

# user inputs
suss_visa_rsrc_name = 'GPIB0::7::INSTR'
# suss_visa_rsrc_name = 'GPIB1::7::INSTR'
suss_visa_timeout_sec = 60
#
z_contact = 12000
z_separate = z_contact - 100
distance_between_mesa = 1300
last_X = 17
last_Y = 17

rm = visa.ResourceManager()
print(rm.list_resources())
suss_resource = rm.open_resource(suss_visa_rsrc_name)
suss = SussPA300(suss_resource, suss_visa_timeout_sec)

suss.velocity = 25
suss.moveZ(z_separate - 1000)
suss.velocity = 5
suss.moveZ(z_separate)
suss.velocity = 1
input('Right click left down edge, set home, right click X1Y1 and press enter.')
(x11_tilled, y11_tilled, _) = suss.read_xyz('H')  # -415.0, -416.0
suss.move_to_xy_from_home(- last_X * distance_between_mesa, 0)
input('Right click X{} Y1, press enter.'.format(last_X))
(x111_tilled, y111_tilled, _) = suss.read_xyz('H')  # -13415.5, -243.0
suss.move_to_xy_from_home(- last_X * distance_between_mesa, - last_Y * distance_between_mesa)
input('Right click substrate top right edge and press enter.')
(xRU_tilled, yRU_tilled, _) = suss.read_xyz('H')  # -13804.5, -5211.5

theta_diagonal_tilled = math.atan(yRU_tilled / xRU_tilled) * 180 / math.pi  # 20.682616056041926
theta_pattern_tilled = math.atan((y111_tilled - y11_tilled) / (x111_tilled - x11_tilled)) * 180 / math.pi  # -0.7624002793812416
theta_diagonal = theta_diagonal_tilled - theta_pattern_tilled  # 21.44501633542317
(x11, y11) = rotate_vector(x11_tilled, y11_tilled, -theta_pattern_tilled)  # -409.42796355219554, -421.4851630383946
x00 = x11 + distance_between_mesa  # 890.5720364478045
y00 = y11 + distance_between_mesa  # 878.5148369616054
x00_subs = -x00
y00_subs = -y00

print(theta_diagonal, x00_subs, y00_subs)
