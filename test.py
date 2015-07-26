import math
import os
import time
import traceback

import visa

from agilent4156c import Agilent4156C
from suss_pa300 import SussPA300

# user inputs
agilent_visa_resource_name = 'GPIB0::18::INSTR'
# agilent_visa_resource_name = 'GPIB1::18::INSTR'
agilent_visa_timeout_sec = 600  # 10min
suss_visa_resource_name = 'GPIB0::7::INSTR'
# suss_visa_resource_name = 'GPIB1::7::INSTR'
suss_visa_timeout_sec = 10


# Initialize
rm = visa.ResourceManager()
print(rm.list_resources())

# a_resource = rm.open_resource(agilent_visa_resource_name)
# a_resource.timeout = agilent_visa_timeout_sec
# print(a_resource.query('*IDN?'))
# a = Agilent4156C(a_resource, False)
# a.idn()


a = Agilent4156C(rm.open_resource(agilent_visa_resource_name), agilent_visa_timeout_sec, False, False)
# c1, c2 = a.contact_test(3, 2, 0.1)
# d1, d2, d3 = a.double_sweep_from_zero(2, 3, 0.01, 0.001)


s = SussPA300(rm.open_resource(suss_visa_resource_name), suss_visa_timeout_sec, False)

def rotate_vector(x, y, theta_deg):
    theta_rad = theta_deg * math.pi/180
    return math.cos(theta_rad)*x - math.sin(theta_rad)*y, math.sin(theta_rad)*x + math.cos(theta_rad)*y


# xy: from home
# GUI inputs
distance_between_mesa = 1300
z_contact = 12000
z_separete = z_contact - 100
# meas_XYs = [(1, 1), (3, 2), (1, 2), (2, 1)]
# meas_XYs = [(X, col) for row in range(1, 5) for col in range(1, 12)]
meas_XYs = [(X, 1) for X in range(1, 12)] + [(X, 2) for X in reversed(range(1, 12))] + [(X, 3) for X in range(1, 12)] + [(X, 4) for X in reversed(range(1, 12))]

# References for calculate theta
tmp = s.read_xyz('C')  # for copy & paste
ref_XYxy1 = [1, 1, -371, -439]
tmp = s.read_xyz('C')  # for copy & paste
ref_XYxy2 = [11, 4, -13206, -4884]
#
ref_delta_X = ref_XYxy2[0] - ref_XYxy1[0]
ref_delta_Y = ref_XYxy2[1] - ref_XYxy1[1]
ref_delta_x = ref_XYxy2[2] - ref_XYxy1[2]
ref_delta_y = ref_XYxy2[3] - ref_XYxy1[3]

# Check distance
d_ref = math.sqrt(ref_delta_x**2 + ref_delta_y**2)
d_calc = math.sqrt((ref_delta_X * distance_between_mesa)**2 + (ref_delta_Y * distance_between_mesa)**2)
print('reference distance: {}'.format(d_ref))
print('calculated distance: {}'.format(d_calc))
if not 0.99 < d_ref/d_calc < 1.01:
    print('wrong distance!')

# Calculate theta
# See document.
theta_vector_subs_rad = math.atan(ref_delta_y / ref_delta_x)
theta_vector_subs_deg = theta_vector_subs_rad * 180 / math.pi
theta_vector_chuck_rad = math.atan(ref_delta_Y / ref_delta_X)
theta_vector_chuck_deg = theta_vector_chuck_rad * 180 / math.pi
theta_deg = theta_vector_subs_deg - theta_vector_chuck_deg

def xy_home_to_subs(x_from_home, y_from_home):
    return rotate_vector(-x_from_home, -y_from_home, -theta_deg)

def xy_subs_to_home(x_subs, y_subs):
    return rotate_vector(-x_subs, -y_subs, theta_deg)

def XY_to_xy_subs(XY, ref_XYxy_from_home):
    ref_xy_subs = xy_home_to_subs(ref_XYxy_from_home[2], ref_XYxy_from_home[3])
    delta_X = XY[0] - ref_XYxy_from_home[0]
    delta_Y = XY[1] - ref_XYxy_from_home[1]
    x = ref_xy_subs[0] + delta_X * distance_between_mesa
    y = ref_xy_subs[1] + delta_Y * distance_between_mesa
    return x, y

mesa = 'D169' # D56.3, D16.7, D5.54
datadir = os.environ['appdata'] + r'\Instr\Agilent4156C'
try:
    for (X, Y) in meas_XYs:
        (x_subs, y_subs) = XY_to_xy_subs((X, Y), ref_XYxy1)
        (x_from_home, y_from_home) = xy_subs_to_home(x_subs, y_subs)
        # input('move z, xy, z!!!!!!!!!!!!!!!!!!!!!!!')
        s.moveZ(z_separete)
        # s.align()
        s.move_to_xy_from_home(x_from_home, y_from_home)
        s.moveZ(z_contact)
        # s.contact()
        # for V in [0.1, -0.1, 0.2, -0.2, 0.3, -0.3, -0.4, 0.4, -0.5, 0.5]:
        for V in [0.2, -0.2]:
            t0 = time.strftime('%Y%m%d-%H%M%S')
            vout, iout, aborted = a.double_sweep_from_zero(2, 1, V, V/1000, 10e-6, 10e-3)
            filename = 'double-sweep_{}_E0326-2-1_X{}_Y{}_{}_{}V.csv'.format(t0, X, Y, mesa, V)
            points = len(vout)
            with open(datadir + '\\' + filename, 'w') as f:
                tmp = [str(elem) for elem in vout]
                tmp = ','.join(tmp)
                f.write(tmp) # v,v,v,v
                f.write('\n')
                tmp = [str(elem) for elem in iout]
                tmp = ','.join(tmp)
                f.write(tmp) # i,i,i,i
                f.write('\n')
            with open(datadir + '\\double-sweep_params.csv', 'a') as f:
                f.write('t0={},sample=E0326-2-1,X={},Y={},xpos={},ypos={},mesa={},status=255,measPoints={},comp=0.01,instr=SUSS PA200, originalFileName={}\n'.
                       format(t0, X, Y, x_subs, y_subs, mesa, points, filename))
                # t0=20150717-125846, sample=E0326-2-1,X=5,Y=3,xpos=5921.5,ypos=3031.5,mesa=D56.3,status=255,measPoints=101,comp=0.01,instr=SUSS PA200, originalFileName=double-sweep_20150717-125846_E0326-2-1_X5_Y3_D56.3_0.1V.csv
            if aborted:
                break
except:
    with open(os.path.expanduser('~') + r'\Dropbox\work\instr_report.txt', 'w') as f:
        f.write(traceback.format_exc() + '\n')
        f.write('\n---------- locals() ----------\n{}\n'.format(locals()))
        f.write('\n---------- globals() ----------\n{}\n'.format(globals()))
    raise
else:
    with open(os.path.expanduser('~') + r'\Dropbox\work\instr_report.txt', 'w') as f:
        f.write('Measurement done.\n')
        f.write('\n---------- locals() ----------\n{}\n'.format(locals()))
        f.write('\n---------- globals() ----------\n{}\n'.format(globals()))
