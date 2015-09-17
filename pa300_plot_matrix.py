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
from lib.algorithms import remove_xyz_by_x


# Configurations ---------------------------------------------------------------
sqlite3_file = os.path.expanduser('~') + '/Documents/instr_data/IV.sqlite3'

# Device data
sample = 'E0326-2-1'
mesa = ['D169', 'D56.3', 'D16.7', 'D5.54'][0]
dia = {'D169': 169e-6, 'D56.3': 56.3e-6, 'D16.7': 16.7e-6, 'D5.54': 5.54e-6}[mesa] # diameter [m]
area = math.pi * (dia/2)**2  # [m^2]

# Bug: Error when (min_X == max_X) or (min_Y == max_Y)
# They must be (min_X < max_X) and (min_Y < max_Y).
min_X, max_X, min_Y, max_Y = (1, 11, 1, 4)

# Plot config
fix_y_range = False
max_V = 0.100
min_V = -0.100
remove_V = 0.020 # for R, RA
var_y = ['J', 'RA', 'R'][0]
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

# Set file name without extension (base)
save_dir = os.path.expanduser('~/Desktop')
if fix_y_range:
    # E0339_D169_RA_1E11_ohmm2_-0.2V_0.2V.png
    save_file_name_base = save_dir + '/{sample}_{mesa}_X{min_X}-{max_X}_Y{min_Y}-{max_Y}_{var_y}_{ylim_nega}_{ylim_pos}_{unit}_{min_V}V_{max_V}V'. \
        format(sample=sample, mesa=mesa, min_X=min_X, max_X=max_X, min_Y=min_Y, max_Y=max_Y, var_y=var_y, unit=unit, ylim_nega=ylim_nega, ylim_pos=ylim_pos, min_V=min_V, max_V=max_V)
else:
    # E0339_D169_RA_auto_ohmm2_-0.2V_0.2V.png
    save_file_name_base = save_dir + '/{sample}_{mesa}_X{min_X}-{max_X}_Y{min_Y}-{max_Y}_{var_y}_auto_{unit}_{min_V}V_{max_V}V'. \
        format(sample=sample, mesa=mesa, min_X=min_X, max_X=max_X, min_Y=min_Y, max_Y=max_Y, var_y=var_y, unit=unit, min_V=min_V, max_V=max_V)
print('Save to: {}.ext'.format(save_file_name_base))

# Connect to database
sqlite3_connection = sqlite3.connect(sqlite3_file)
cursor = sqlite3_connection.cursor()


# Plot -------------------------------------------------------------------------
print('Making subplots frame...')
# Takes long time. figsize: inches. (300dpi -> about (300numX px, 300numY px)
f, axarr = plt.subplots(numY, numX, figsize=(numX, numY), facecolor='w')
if fix_y_range:
    f.subplots_adjust(top=1, bottom=0, left=0, right=1, wspace=0, hspace=0)
else:
    f.subplots_adjust(top=0.99, bottom=0.01, left=0.01, right=0.99, wspace=0, hspace=0)

for Y in range(min_Y, max_Y + 1):
    for X in range(min_X, max_X + 1):
        print('Processing X{}Y{}.'.format(X, Y))
        t0s = cursor.execute('SELECT t0 FROM parameters WHERE sample=? AND mesa=? AND X=? AND Y=?',
                             (sample, mesa, X, Y)).fetchall()

        # rowi coli X Y matrix (if num_X = num_Y = 9)
        # 00XminYmax     ...                90XmaxYmax
        # ...
        # 80Xmin(Ymin+1) ...
        # 90XminYmin     91(Xmin+1)Ymin ... 99XmaxYmin
        coli = -min_X + X
        rowi = max_Y - Y
        ax = axarr[rowi, coli]

        if t0s == []:
            print('No data on X{}Y{} (rowi{}coli{})'.format(X, Y, rowi, coli))
            # No tick
            ax.set_xticks([])
            ax.set_yticks([])
            continue
        
        if var_y in ['J', 'dJdV']:
            #ax.locator_params(nbins=5)  # number of ticks
            ax.set_yticks([0])  # tick only zero level
            ax.yaxis.set_major_formatter(plt.NullFormatter())  # Hide value of ticks
        elif var_y in ['R', 'RA']:
            ax.set_yticks([0])
            ax.yaxis.set_major_formatter(plt.NullFormatter())
            #ax.get_yaxis().get_major_formatter().set_powerlimits((0, 0))  # Force exponential ticks

        # Get data XY
        xs = np.array([])  # x axis values
        ys = np.array([])  # y axis values
        for t0 in t0s:
            VIs_new = cursor.execute('SELECT V, I FROM IV WHERE t0=?', t0).fetchall() # Be sure that t0 has index (else slow)
            VIs_new = np.array(VIs_new)
            if var_y in ['RA', 'R']:
                VIs_new = remove_X_near_0(VIs_new, remove_V)  # TODO: auto determine divergence near 0
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
            elif var_y == 'dJdV':
                dJdV_new = np.gradient(Js_new, Vs_new)  # TODO: implement
                ys = np.append(ys, dJdV_new)
        xys_in_range = remove_xyz_by_x(lambda x: not min_V < x < max_V, xs, ys)
        ys_in_range = xys_in_range[1]

        # Plot
        #ax.plot(xs, ys, 'b', linewidth=0.5)
        ax.scatter(xs, ys, s=0.1, c=list(range(len(xs))), cmap=cm.rainbow, edgecolor='none')  # s: size

        ax.set_xticks([])
        ax.set_xlim([min_V, max_V])
        if fix_y_range:
            ax.set_yticks([])
            ax.set_ylim([-float(ylim_nega), float(ylim_pos)])
        elif var_y in ['J', 'dJdV']:
            # Symmetric y limits with respect to y=0
            y_abs_max = max(abs(ys_in_range))
            ax.set_ylim([-y_abs_max, y_abs_max])
            y_lim_txt = '{:.1E}'.format(y_abs_max).replace('E', '\nE')  # 1.23 \n E+4
            # ha: horizontal alignment, va: vertical alignment, transAxes: relative coordinates
            ax.text(0.01, 0.99, y_lim_txt, ha='left', va='top', transform=ax.transAxes)
        elif var_y in ['R', 'RA']:
            # Assuming ys > 0
            y_min = min(ys_in_range)  # TODO: use ys only V_min-V_max
            y_max = max(ys_in_range)
            y_range = y_max - y_min
            if not float('Inf') in [y_min, y_max]:
                ax.set_ylim([y_min - 0.1*y_range, y_max + 0.1*y_range])
            y_lim_txt_top = '{:.1E}'.format(y_max).replace('E', '\nE')  # 1.23 \n E+4
            ax.text(0.01, 0.99, y_lim_txt_top, ha='left', va='top', transform=ax.transAxes)
            y_lim_txt_bottom = '{:.1E}'.format(y_min).replace('E', '\nE')
            ax.text(0.01, 0.01, y_lim_txt_bottom, ha='left', va='bottom', transform=ax.transAxes)
            

print('Saving', save_file_name_base + '.png')
plt.savefig(save_file_name_base + '.png', dpi=600, transparent=True)
#print('Saving', save_file_name_base + '.pdf')
#plt.savefig(save_file_name_base + '.pdf', transparent=True)  # dpi is ignored, transparent as well?
