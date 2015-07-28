import math
import visa
from suss_pa300 import SussPA300


def rotate_vector(x, y, theta_deg):
    theta_rad = theta_deg * math.pi/180
    return math.cos(theta_rad)*x - math.sin(theta_rad)*y, math.sin(theta_rad)*x + math.cos(theta_rad)*y

# !!!! Up prober !!!!
# user inputs
suss_visa_resource_name = 'GPIB0::7::INSTR'
# suss_visa_resource_name = 'GPIB1::7::INSTR'
suss_visa_timeout_sec = 60
#
subs_width = 13500  # approximately
subs_height = 4500
z_contact = 12000
z_separete = z_contact - 100
distance_between_mesa = 1300

try:
    rm = visa.ResourceManager()
    print(rm.list_resources())
    suss_resource = rm.open_resource(suss_visa_resource_name)
    suss = SussPA300(suss_resource, suss_visa_timeout_sec)

    # suss.moveZ(z_separete)
    input('Set LD home and right click X1Y1 then press enter.')
    (x11_tilled, y11_tilled, _) = suss.read_xyz('H')
    suss.move_to_xy_from_home(subs_width, 0)
    input('Right click X11Y1, press enter.')
    (x111_tilled, y111_tilled, _) = suss.read_xyz('H')
    suss.move_to_xy_from_home(subs_width, subs_height)
    input('Right click substrate RU, press enter.')
    (xRU_tilled, yRU_tilled, _) = suss.read_xyz('H')
except:
    (x11_tilled, y11_tilled) = [int(elem) for elem in input('Set LD home and input x y of X1Y1.').split()]
    (x111_tilled, y111_tilled) = [int(elem) for elem in input('Input x y of X11Y1.').split()]
    (xRU_tilled, yRU_tilled) = [int(elem) for elem in input('Input x y of substrate RU.').split()]

theta_diagonal_tilled = math.atan(yRU_tilled / xRU_tilled) * 180 / math.pi
theta_pattern_tilld = math.atan((y111_tilled - y11_tilled) / (x111_tilled - x11_tilled)) * 180 / math.pi
theta_diagonal = theta_diagonal_tilled - theta_pattern_tilld
(x11, y11) = rotate_vector(x11_tilled, y11_tilled, -theta_pattern_tilld)
x00 = x11 - distance_between_mesa
y00 = y11 - distance_between_mesa
print(theta_diagonal, x00, y00)
