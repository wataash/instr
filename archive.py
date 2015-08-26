# old code
import os

conf = {}

# VISA configurations
conf['agi_visa_rsrc_name'] = 'GPIB0::18::INSTR'  # 'GPIB1::18::INSTR'
conf['agi_visa_timeout_sec'] = 600  # 10min
conf['suss_visa_rsrc_name'] = 'GPIB0::7::INSTR'  # 'GPIB1::7::INSTR'
conf['suss_visa_timeout_sec'] = 10

# Directory
conf['data_dir'] = os.environ['appdata'] + r'\Instr\Agilent4156C'

# Device information
conf['sample'] = 'E0325t-1-1'
conf['mesa'] = 'D56.3'
conf['distance_between_mesa'] = 1300
conf['max_X'] = 4
conf['max_Y'] = 4
conf['subs_width'] = 6500  # approximately
conf['subs_height'] = 6500  # approx

# Use theta.py
(conf['theta_diagonal'], conf['x00_subs'], conf['y00_subs']) = (43.9395886298078, -353.9133081057827, -23.85219452421734)  # D169

# Measurement configurations
conf['z_contact'] = 12000
conf['z_separate'] = conf['z_contact'] - 100

# meas_XYs = [(1, 1), (3, 2), (1, 2), (2, 1)]
conf['meas_XYs'] = [(X, 1) for X in range(3, conf['max_X']+1)] + [(X, 2) for X in reversed(range(1, conf['max_X']+1))] + \
           [(X, 3) for X in range(1, conf['max_X']+1)] + [(X, 4) for X in reversed(range(1, conf['max_X']+1))]

# meas_Vs = [0.1, -0.1, 0.2, -0.2, 0.3, -0.3, -0.4, 0.4, -0.5, 0.5]
conf['meas_Vs'] = [0.1, -0.1]



# data write
# with open(conf['data_dir'] + '\\' + filename, 'w') as f:
#     Vs = [str(elem) for elem in Vs]
#     Vs = ','.join(Vs)
#     f.write(Vs)  # V, V, V, ... TODO: transpose
#     f.write('\n')
#     Is = [str(elem) for elem in Is]
#     Is = ','.join(Is)
#     f.write(Is)  # I, I, I, ... TODO: transpose
#     f.write('\n')

# with open(conf['data_dir'] + '\\double-sweep_params.csv', 'a') as f:
#     f.write('t0={},sample=E0326-2-1,X={},Y={},xpos={},ypos={},mesa={},status=255,measPoints={},comp=0.01,instr=SUSS PA300, originalFileName={}\n'.
#            format(t0, X, Y, x_next_subs, y_next_subs, conf['mesa'], points, filename))
    # t0=20150717-125846, sample=E0326-2-1,X=5,Y=3,xpos=5921.5,ypos=3031.5,mesa=D56.3,status=255,measPoints=101,comp=0.01,instr=SUSS PA300, originalFileName=double-sweep_20150717-125846_E0326-2-1_X5_Y3_D56.3_0.1V.csv