# old code
import os

# User inputs ------------------------------------------------------------------
# VISA configurations
agilent_visa_resource_name = 'GPIB0::18::INSTR'  # 'GPIB1::18::INSTR'
agilent_visa_timeout_sec = 600  # 10min
suss_visa_resource_name = 'GPIB0::7::INSTR'  # 'GPIB1::7::INSTR'
suss_visa_timeout_sec = 10
# Directory
datadir = os.environ['appdata'] + r'\instr\Agilent4156C'
# Device information
sample = 'sample # 2'
mesa = 'D56.3'
distance_between_mesa = 1300
last_X = 4
last_Y = 4
subs_width = 6500  # approximately
subs_height = 6500  # approx
# Use theta.py
(theta_diagonal, x00_subs, y00_subs) = (43.9395886298078, -353.9133081057827, -23.85219452421734)  # D169
if mesa == 'D56.3':
    x00_subs += 300
if mesa == 'D16.7':
    x00_subs += 600
if mesa == 'D5.54':
    x00_subs += 900
# Measurement configurations
z_contact = 12000
z_separate = z_contact - 100
# meas_XYs = [(1, 1), (3, 2), (1, 2), (2, 1)]
meas_XYs = [(X, 1) for X in range(3, last_X+1)] + [(X, 2) for X in reversed(range(1, last_X+1))] + \
           [(X, 3) for X in range(1, last_X+1)] + [(X, 4) for X in reversed(range(1, last_X+1))]
# meas_Vs = [0.1, -0.1, 0.2, -0.2, 0.3, -0.3, -0.4, 0.4, -0.5, 0.5]
meas_Vs = [0.1, -0.1]





# VISA configurations
conf['agilent_visa_resource_name'] = 'GPIB0::18::INSTR'  # 'GPIB1::18::INSTR'
conf['agilent_visa_timeout_sec'] = 600  # 10min
conf['suss_visa_resource_name'] = 'GPIB0::7::INSTR'  # 'GPIB1::7::INSTR'
conf['suss_visa_timeout_sec'] = 10

# Directory
conf['datadir'] = os.environ['appdata'] + r'\Instr\Agilent4156C'

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