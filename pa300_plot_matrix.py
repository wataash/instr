import json
import math
import os
import sqlite3

import matplotlib.pyplot as plt
import numpy as np

from lib.algorithms import remove_X_near_0


# Configurations ---------------------------------------------------------------
sqlite3_file = os.path.expanduser('~') + '/Documents/instr_data/IV.sqlite3'

sample = "E0339"
mesa = ['D169', 'D56.3', 'D16.7', 'D5.54'][0]
dia = float(mesa[1:]) * 1e-6  # [m]
area = math.pi * (dia/2)**2  # [m^2]

min_X = 1
max_X = 2
min_Y = 1
max_Y = 2

fix_y_range = False
max_V = 0.2
min_V = -0.2
unit =      ['Am2', 'ohmm2', 'ohm'][0]
ylim_nega =     ['-1E-5', '0', '0'][0]
ylim_pos =  ['1E-5', '1E-1', '1E6'][0]
var_y =            ['J', 'RA', 'R'][0]

# Number of columns and rows in matrix plot
numX = max_X - min_X + 1
numY = max_Y - min_Y + 1


# Connect to database ----------------------------------------------------------
sqlite3_connection = sqlite3.connect(sqlite3_file)
cursor = sqlite3_connection.cursor()

png_file_name = os.path.expanduser('~')
if fix_y_range:
    # E0339_D169_RA_1E11_ohmm2_-0.2V_0.2V.png
    png_file_name += '/Desktop/{sample}_{mesa}_{var_y}_{ylim_nega}_{ylim_pos}_{unit}_-0.2V_0.2V.png'. \
        format(sample=sample, mesa=mesa, var_y=var_y, unit=unit, ylim_nega=ylim_nega, ylim_pos=ylim_pos)
else:
    # E0339_D169_RA_auto_ohmm2_-0.2V_0.2V.png
    png_file_name += '/Desktop/{sample}_{mesa}_{var_y}_auto_{unit}_-0.2V_0.2V.png'. \
        format(sample=sample, mesa=mesa, var_y=var_y, unit=unit)

# Plot -------------------------------------------------------------------------
f, axarr = plt.subplots(numY, numX, figsize=(numX, numY), facecolor='w')  # Takes long time
if fix_y_range:
    f.subplots_adjust(top=1, bottom=0, left=0, right=1, wspace=0, hspace=0)

for Y in range(min_Y, max_Y + 1):
    for X in range(min_X, max_X + 1):
        print('Execute SQLite command (X={}, Y={})'.format(X, Y))
        t0s = cursor.execute('''
            SELECT t0 FROM parameters
            WHERE sample=? AND mesa=? AND X=? AND Y=?
            ''', (sample, mesa, X, Y)).fetchall()

        # Slow because of searching in all data in IV
        #    cursor.execute('''
        #    SELECT V, I FROM IV
        #    INNER JOIN parameters ON IV.t0=parameters.t0
        #    WHERE sample=? AND mesa=? AND X=? AND Y=?
        #    ''', (sample, mesa, X, Y)).fetchall()

        # rowi coli X Y matrix (if num_X = num_Y = 9)
        # 00XminYmax     ...                90XmaxYmax
        # ...
        # 80Xmin(Ymin+1) ...
        # 90XminYmin     91(Xmin+1)Ymin ... 99XmaxYmin
        print('Configure plot t0s=', t0s)
        coli = -min_X + X  # privious: -X TODO check
        rowi = max_Y - Y
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
            axarr[rowi, coli].set_xlim([min_V, max_V])
            if fix_y_range:
                axarr[rowi, coli].set_yticks([])
                axarr[rowi, coli].set_ylim([-float(ylim_nega), float(ylim_pos)])

        if t0s == []:
            axarr[rowi, coli].set_xticks([])
            axarr[rowi, coli].set_yticks([])


plt.savefig(png_file_name, dpi=300, transparent=True)
