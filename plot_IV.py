from collections import defaultdict
import json
import math
import os
import sqlite3

import matplotlib.pyplot as plt
import numpy as np


# Prefix 'd': dictionary


# Configurations ---------------------------------------------------------------
#conf = defaultdict(str)
conf = {}
os.makedirs(os.environ['appdata'] + r'\instr', exist_ok=True)

if os.path.isfile(os.environ['appdata'] + r'\instr\plot_IV_conf.json'):
    with open(os.environ['appdata'] + r'\instr\plot_IV_conf.json') as f:
        #conf = defaultdict(str, json.load(f))
        conf = json.load(f)
else:
    with open(r'dummy_data\plot_IV_conf.json') as f:
        #conf = defaultdict(str, json.load(f))
        conf = json.load(f)


# Calculations -----------------------------------------------------------------
area = math.pi * (conf['dia']/2)**2  # um^2
numX = conf['Xmax'] - conf['Xmin'] + 1
numY = conf['Ymax'] - conf['Ymin'] + 1


# Connect to database ----------------------------------------------------------
sqlite3_connection = sqlite3.connect(conf['sqlite3_file'])
cursor = sqlite3_connection.cursor()


# Plot -------------------------------------------------------------------------
f, axarr = plt.subplots(numY, numX, figsize=(numX, numY), facecolor='w')  # Takes long time
f.subplots_adjust(top=1, bottom=0, left=0, right=1, wspace=0, hspace=0)

for Y in range(conf['Xmin'], conf['Xmax'] + 1):
    for X in range(conf['Ymin'], conf['Ymax'] + 1):
        print('execute')
        t0s = cursor.execute('''
            SELECT t0 FROM parameters
            WHERE sample=? AND mesa=? AND X=? AND Y=?
            ''', (conf['sample'], conf['mesa'], X, Y)).fetchall()
        print('t0s:', t0s)

        # Slow because of searching in all data in IV
        #    cursor.execute('''
        #    SELECT V, I FROM IV
        #    INNER JOIN parameters ON IV.t0=parameters.t0
        #    WHERE sample=? AND mesa=? AND X=? AND Y=?
        #    ''', (conf['sample'], conf['mesa'], X, Y)).fetchall()

        if t0s == []:
            continue

        for t0 in t0s:
            tmp = cursor.execute('SELECT V, I FROM IV WHERE t0=?', t0).fetchall()
            #(V, I) = zip(*tmp)  # TODO: speed test. faster than numpy?
            print('np')
            VIs = np.array(tmp)
            V = VIs.transpose()[0]
            J = VIs.transpose()[1]/area
            RA = V/J

            # rowi coli X Y matrix (if num_X = num_Y = 9)
            # 00XminYmax     ...                90XmaxYmax
            # ...
            # 80Xmin(Ymin+1) ...
            # 90XminYmin     91(Xmin+1)Ymin ... 99XmaxYmin
            coli = -conf['Xmin'] + X  # privious: -X TODO check
            rowi = conf['Ymax'] - Y

            print('plot')
            axarr[rowi, coli].plot(V, J, 'b', linewidth=0.2)
            #axarr[rowi, coli].plot(V, RA, 'r', linewidth=0.2)
            #axarr[rowi, coli].plot(V, np.gradient(J, V), 'b', linewidth=0.1)
            axarr[rowi, coli].set_xticks([])
            axarr[rowi, coli].set_yticks([])
            axarr[rowi, coli].set_xlim([conf['plot_V_min'], conf['plot_V_max']])
            # axarr[rowi, coli].set_ylim([-1e-11, 1e-11])  # J [A/um^2]
            # axarr[rowi, coli].set_ylim([0, 2e12])  # RA [ohm um^2]
            #axarr[rowi, coli].set_ylim([-1e-13, 1e-13])  # dJ/dV [A/um^2/V]

plt.savefig(os.path.expanduser('~') + r'\Desktop\tmp.png', dpi=300, transparent=True)
