# Std libs
from collections import defaultdict
import math
import os
import sqlite3
# Non-std libs
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
# My libs
from lib.algorithms import remove_X_near_0


# Fast debag mode (SQL query is slow if database is large)
debug_mode = False
if debug_mode:
    print('*'*20, 'Debug mode', '*'*20)

# Configurations ---------------------------------------------------------------
sqlite3_file = os.path.expanduser('~') + '/Documents/instr_data/IV.sqlite3'

# Device data
sample = 'E0326-2-1'
mesa = ['D169', 'D56.3', 'D16.7', 'D5.54'][1]
dia = {'D169': 169e-6, 'D56.3': 56.3e-6, 'D16.7': 16.7e-6, 'D5.54': 5.54e-6}[mesa] # diameter [m]
area = math.pi * (dia/2)**2  # [m^2]

# Bug: Error when (min_X == max_X) or (min_Y == max_Y)
# They must be (min_X < max_X) and (min_Y < max_Y).
min_X, max_X, min_Y, max_Y = (1, 11, 1, 4)

# Plot config
fix_y_range = False
max_V = 0.1
min_V = -0.1
var_y = ['J', 'RA', 'R'][2]
dict_unit = {'J': 'Am2', 'RA': 'ohmm2', 'R': 'ohm'}
dict_ylim_nega = {'J': '-1E-5', 'RA': '0', 'R': '0'}
dict_ylim_pos = {'J': '1E-5', 'RA': '1E-1', 'R': '1E6'}


# Calculations -----------------------------------------------------------------


# Number of columns and rows in matrix plot
numX = max_X - min_X + 1
numY = max_Y - min_Y + 1

unit = dict_unit[var_y]
ylim_nega = dict_ylim_nega[var_y]
ylim_pos = dict_ylim_pos[var_y]

png_file_name = os.path.expanduser('~')
if fix_y_range:
    # E0339_D169_RA_1E11_ohmm2_-0.2V_0.2V.png
    png_file_name += '/Desktop/{sample}_{mesa}_X{min_X}-{max_X}_Y{min_Y}-{max_Y}_{var_y}_{ylim_nega}_{ylim_pos}_{unit}_{min_V}V_{max_V}V.png'. \
        format(sample=sample, mesa=mesa, min_X=min_X, max_X=max_X, min_Y=min_Y, max_Y=max_Y, var_y=var_y, unit=unit, ylim_nega=ylim_nega, ylim_pos=ylim_pos, min_V=min_V, max_V=max_V)
else:
    # E0339_D169_RA_auto_ohmm2_-0.2V_0.2V.png
    png_file_name += '/Desktop/{sample}_{mesa}_X{min_X}-{max_X}_Y{min_Y}-{max_Y}_{var_y}_auto_{unit}_{min_V}V_{max_V}V.png'. \
        format(sample=sample, mesa=mesa, min_X=min_X, max_X=max_X, min_Y=min_Y, max_Y=max_Y, var_y=var_y, unit=unit, min_V=min_V, max_V=max_V)
print('Save to:', png_file_name)

# Connect to database
if not debug_mode:
    sqlite3_connection = sqlite3.connect(sqlite3_file)
    cursor = sqlite3_connection.cursor()


# Plot -------------------------------------------------------------------------
print('Making subplots frame...')
f, axarr = plt.subplots(numY, numX, figsize=(numX, numY), facecolor='w')  # Takes long time
if fix_y_range:
    f.subplots_adjust(top=1, bottom=0, left=0, right=1, wspace=0, hspace=0)

for Y in range(min_Y, max_Y + 1):
    for X in range(min_X, max_X + 1):
        print('Processing X{}Y{}.'.format(X, Y))
        if debug_mode:
            t0s = [1234]
        else:
            print('Executing SQLite command.')
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
        coli = -min_X + X
        rowi = max_Y - Y

        if t0s == []:
            print('No data on X{}Y{} (rowi{}coli{})'.format(X, Y, rowi, coli))
            # No tick
            axarr[rowi, coli].set_xticks([])
            axarr[rowi, coli].set_yticks([])
            continue

        print('Configuring plot for t0s =', t0s)
        axarr[rowi, coli].locator_params(nbins=5)  # number of ticks
        axarr[rowi, coli].get_yaxis().get_major_formatter().set_powerlimits((0, 0))  # Force exponential ticks

        # Get data XY
        xs = np.array([])  # x axis values
        ys = np.array([])  # y axis values
        for t0 in t0s:
            print('Querying data.')
            if debug_mode:
                VIs_new = [[V, (1e-5 + 1e-6*X)*(V + 0.1*V**2) + 1e-7*Y*math.sin(Y*V/max_V)] for V in np.linspace(min_V, max_V, 101)]
            else:
                VIs_new = cursor.execute('SELECT V, I FROM IV WHERE t0=?', t0).fetchall() # Slow (~1sec)
            print('Got data.')
            VIs_new = np.array(VIs_new)
            if var_y in ['RA', 'R']:
                VIs_new = remove_X_near_0(VIs_new, 10e-3)
            Vs_new = VIs_new.transpose()[0]
            xs = np.append(xs, Vs_new)
            Js_new = VIs_new.transpose()[1]/area
            if var_y == 'J':
                ys = np.append(ys, Js_new)
            elif var_y == 'RA':
                RAs_new = Vs_new/Js_new
                ys = np.append(ys, RAs_new)
            elif var_y == 'R':
                Rs_new = Vs_new/(Js_new*area)
                ys = np.append(ys, Rs_new)

        ## Plot data XY
        #print('Plotting t0 =', t0)
        #if var_y == 'J':
        #    axarr[rowi, coli].plot(Vs, Js, 'b', linewidth=0.5)
        #elif var_y == 'RA':
        #    axarr[rowi, coli].plot(Vs, RAs, 'r', linewidth=0.5)
        #elif var_y == 'R':
        #    axarr[rowi, coli].plot(Vs, Rs, 'r', linewidth=0.5)
        #elif var_y == 'dJdV':
        #    axarr[rowi, coli].plot(Vs, np.gradient(Js, Vs), 'b', linewidth=0.1)

        # Scatter XY
        print('Plotting t0 =', t0)

        axarr[rowi, coli].scatter(xs, ys, s=0.1, c=list(range(len(xs))), cmap=cm.rainbow, edgecolor='none')  # s: size

        axarr[rowi, coli].set_xticks([])
        axarr[rowi, coli].set_xlim([min_V, max_V])
        if fix_y_range:
            axarr[rowi, coli].set_yticks([])
            axarr[rowi, coli].set_ylim([-float(ylim_nega), float(ylim_pos)])

        print()  # newline


plt.savefig(png_file_name, dpi=300, transparent=True)
plt.savefig(png_file_name.replace('.png', '.pdf'), transparent=True)  # dpi is ignored, transparent as well?
