from collections import defaultdict
import json
import math
import os
import sqlite3

import matplotlib.pyplot as plt
import numpy as np

from lib.algorithms import remove_X_near_0


# Configurations ---------------------------------------------------------------
#conf = defaultdict(str)
conf = {}
if os.path.isfile(os.environ['appdata'] + r'\instr\plot_IV_conf.json'):
    with open(os.environ['appdata'] + r'\instr\plot_IV_conf.json') as f:
        #conf = defaultdict(str, json.load(f))
        conf = json.load(f)
else:
    with open(r'dummy_data\plot_IV_conf.json') as f:
        #conf = defaultdict(str, json.load(f))
        conf = json.load(f)


# Calculations -----------------------------------------------------------------
area = math.pi * (conf['dia']/2)**2  # m^2
numX = conf['Xmax'] - conf['Xmin'] + 1
numY = conf['Ymax'] - conf['Ymin'] + 1


# Connect to database ----------------------------------------------------------
sqlite3_connection = sqlite3.connect(conf['sqlite3_file'])
cursor = sqlite3_connection.cursor()


# Plot -------------------------------------------------------------------------
is_y_fixed_range = False
var_y = 'RA'
#var_y = 'J'
#var_y = 'R'
d_ylim = {'J': '1E-10', 'RA': '1E10', 'R': '1E6'}
d_unit = {'J': 'Am2', 'RA': 'ohmm2', 'R': 'ohm'}

f, axarr = plt.subplots(numY, numX, figsize=(numX, numY), facecolor='w')  # Takes long time
if is_y_fixed_range:
    f.subplots_adjust(top=1, bottom=0, left=0, right=1, wspace=0, hspace=0)

for Y in range(conf['Ymin'], conf['Ymax'] + 1):
    for X in range(conf['Xmin'], conf['Xmax'] + 1):
        print('Execute SQLite command (X={}, Y={})'.format(X, Y))
        t0s = cursor.execute('''
            SELECT t0 FROM parameters
            WHERE sample=? AND mesa=? AND X=? AND Y=?
            ''', (conf['sample'], conf['mesa'], X, Y)).fetchall()


        # Slow because of searching in all data in IV
        #    cursor.execute('''
        #    SELECT V, I FROM IV
        #    INNER JOIN parameters ON IV.t0=parameters.t0
        #    WHERE sample=? AND mesa=? AND X=? AND Y=?
        #    ''', (conf['sample'], conf['mesa'], X, Y)).fetchall()

        # rowi coli X Y matrix (if num_X = num_Y = 9)
        # 00XminYmax     ...                90XmaxYmax
        # ...
        # 80Xmin(Ymin+1) ...
        # 90XminYmin     91(Xmin+1)Ymin ... 99XmaxYmin
        print('Configure plot t0s=', t0s)
        coli = -conf['Xmin'] + X  # privious: -X TODO check
        rowi = conf['Ymax'] - Y
        axarr[rowi, coli].locator_params(nbins=5)  # number of ticks
        axarr[rowi, coli].get_yaxis().get_major_formatter().set_powerlimits((0, 0))  # Force exponential ticks

        for t0 in t0s:
            tmp = cursor.execute('SELECT V, I FROM IV WHERE t0=?', t0).fetchall()
            #(V, I) = zip(*tmp)  # TODO: speed test. faster than numpy?
            print('numpy t0=', t0)
            VIs = np.array(tmp)
            if var_y in ['RA', 'R']:
                VIs = remove_X_near_0(VIs, 10e-3)
            V = VIs.transpose()[0]
            J = VIs.transpose()[1]/area
            if var_y == 'RA':
                RA = V/J
            elif var_y == 'R':
                R = V/(J*area)

            print('plot')
            if var_y == 'J':
                axarr[rowi, coli].plot(V, J, 'b', linewidth=0.5)
            elif var_y == 'RA':
                axarr[rowi, coli].plot(V, RA, 'r', linewidth=0.5)
            elif var_y == 'R':
                axarr[rowi, coli].plot(V, R, 'r', linewidth=0.5)
            elif var_y == 'dJdV':
                axarr[rowi, coli].plot(V, np.gradient(J, V), 'b', linewidth=0.1)

            axarr[rowi, coli].set_xticks([])
            axarr[rowi, coli].set_xlim([conf['plot_V_min'], conf['plot_V_max']])
            if is_y_fixed_range:
                axarr[rowi, coli].set_yticks([])
                axarr[rowi, coli].set_ylim([-float(d_ylim[var_y]), float(d_ylim[var_y])])

        if t0s == []:
            axarr[rowi, coli].set_xticks([])
            axarr[rowi, coli].set_yticks([])

file_name = os.path.expanduser('~')
if is_y_fixed_range:
    # E0339_D169_RA_1E11_ohmm2_-0.2V_0.2V.png
    file_name += '/Desktop/{sample}_{mesa}_{var_y}_{ylim}_{unit}_-0.2V_0.2V.png'. \
        format(sample=conf['sample'], mesa=conf['mesa'], var_y=var_y, unit=d_unit[var_y], ylim=d_ylim[var_y])
else:
    # E0339_D169_RA_auto_ohmm2_-0.2V_0.2V.png
    file_name += '/Desktop/{sample}_{mesa}_{var_y}_auto_{unit}_-0.2V_0.2V.png'. \
        format(sample=conf['sample'], mesa=conf['mesa'], var_y=var_y, unit=d_unit[var_y], ylim=d_ylim[var_y])

plt.savefig(file_name, dpi=300, transparent=True)
