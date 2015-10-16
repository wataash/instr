# Std libs
from collections import defaultdict
import json
import math
import os
import sqlite3
# Non-std libs
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
# My libs
import constants as c
from lib.algorithms import remove_X_near_0
from lib.algorithms import remove_xyz_by_x


# TODO: V_min, V_max from SQL

conn_params = sqlite3.connect(c.sql_params_dropbox)
conn_IVs = sqlite3.connect(c.p_sql_IVs)
cur_params = conn_params.cursor()
cur_IVs = conn_IVs.cursor()

X_min, X_max, Y_min, Y_max = \
    cur_params.execute('SELECT sample, min_X, max_X, min_Y, max_Y \
                        FROM samples WHERE sample=?',
                        (c.p_sample,)
                      ).fetchone()
area = \
    cur_params.execute('SELECT area \
                        FROM mesas WHERE mesa=?',
                        (c.p_mesa,)
                      ).fetchone()

# Number of columns and rows in matrix plot
numX = X_max - X_min + 1
numY = Y_max - Y_min + 1

# Set png file name
save_dir = os.path.expanduser('~/Desktop')
if c.p_fix_y:
    # E0339_D169_RA_1E11_ohmm2_-0.2V_0.2V.png
    save_file_name_base = save_dir + '/{sample}_{mesa}_X{X_min}-{X_max}_Y{Y_min}-{Y_max}_{var_y}_{ylim_nega}_{ylim_pos}_{unit}_{min_V}V_{max_V}V.png'. \
        format(sample=c.p_sample, mesa=c.p_mesa, X_min=X_min, X_max=X_max, Y_min=Y_min, Y_max=Y_max, var_y=c.p_var_y, unit=c.p_unit, ylim_nega=c.p_ylim_nega, ylim_pos=c.p_ylim_pos, min_V=V_min, max_V=V_max)
else:
    # E0339_D169_RA_auto_ohmm2_-0.2V_0.2V.png
    save_file_name_base = save_dir + '/{sample}_{mesa}_X{X_min}-{X_max}_Y{Y_min}-{Y_max}_{var_y}_auto_{unit}_{min_V}V_{max_V}V.png'. \
        format(sample=c.p_sample, mesa=c.p_mesa, X_min=X_min, X_max=X_max, Y_min=Y_min, Y_max=Y_max, var_y=c.p_var_y, unit=c.p_unit, min_V=V_min, max_V=V_max)
print('Save to:', save_file_name_base)


# Plot -------------------------------------------------------------------------
print('Making subplots frame...')
# Takes long time. figsize: inches. (300dpi -> about (300*numX px, 300*numY px)
# Bug: Error when (X_min == X_max) or (Y_min == Y_max) at axarr[rowi, coli]
# They must be (X_min < X_max) and (Y_min < Y_max).
f, axarr = plt.subplots(numY, numX, figsize=(numX, numY), facecolor='w')
if c.p_fix_y:
    f.subplots_adjust(top=1, bottom=0, left=0, right=1, wspace=0, hspace=0)
else:
    f.subplots_adjust(top=0.99, bottom=0.01, left=0.01, right=0.99, wspace=0, hspace=0)

for Y in range(Y_min, Y_max + 1):
    for X in range(X_min, X_max + 1):
        print('Processing X{}Y{}.'.format(X, Y))
        t0s = cur_params.execute('SELECT t0 FROM params WHERE sample=? AND mesa=? AND X=? AND Y=?',
                                  (sample, mesa, X, Y)).fetchall()

        # rowi coli X Y matrix (if num_X = num_Y = 9)
        # 00XminYmax     ...                90XmaxYmax
        # ...
        # 80Xmin(Ymin+1) ...
        # 90XminYmin     91(Xmin+1)Ymin ... 99XmaxYmin
        coli = -X_min + X
        rowi = Y_max - Y
        ax = axarr[rowi, coli]

        if t0s == []:
            print('No data on X{}Y{} (rowi{}coli{})'.format(X, Y, rowi, coli))
            # No tick
            ax.set_xticks([])
            ax.set_yticks([])
            continue
        
        if c.p_var_y in ['J', 'dJdV']:
            #ax.locator_params(nbins=5)  # number of ticks
            ax.set_yticks([0])  # tick only zero level
            ax.yaxis.set_major_formatter(plt.NullFormatter())  # Hide value of ticks
        elif c.p_var_y in ['R', 'RA']:
            ax.set_yticks([0])
            ax.yaxis.set_major_formatter(plt.NullFormatter())
            #ax.get_yaxis().get_major_formatter().set_powerlimits((0, 0))  # Force exponential ticks

        # Get data XY
        xs = np.array([])  # x axis values
        ys = np.array([])  # y axis values
        for t0 in t0s:
            VIs_new = cur_IVs.execute('SELECT V, I FROM IVs WHERE t0=?', t0).fetchall() # Be sure that t0 has index (else slow)
            VIs_new = np.array(VIs_new)
            if c.p_var_y in ['RA', 'R']:
                VIs_new = remove_X_near_0(VIs_new, c.p_remove_V)  # TODO: auto determine divergence near 0
            Vs_new = VIs_new.transpose()[0]
            xs = np.append(xs, Vs_new)
            Js_new = VIs_new.transpose()[1]/area
            if c.p_var_y == 'J':
                ys = np.append(ys, Js_new)
            elif c.p_var_y == 'RA':
                RAs_new = Vs_new/Js_new
                ys = np.append(ys, RAs_new)
            elif c.p_var_y == 'R':
                Rs_new = Vs_new/(Js_new*area)
                ys = np.append(ys, Rs_new)
            elif c.p_var_y == 'dJdV':
                dJdV_new = np.gradient(Js_new, Vs_new)  # TODO: implement
                ys = np.append(ys, dJdV_new)
        xys_in_range = remove_xyz_by_x(lambda x: not V_min < x < V_max, xs, ys)
        ys_in_range = xys_in_range[1]

        # Plot
        #ax.plot(xs, ys, 'b', linewidth=0.5)
        ax.scatter(xs, ys, s=1, c=list(range(len(xs))), cmap=cm.rainbow, edgecolor='none')  # s: size

        ax.set_xticks([])
        ax.set_xlim([V_min, V_max])
        if c.p_fix_y:
            ax.set_yticks([])
            ax.set_ylim([-float(c.p_ylim_nega), float(c.p_ylim_pos)])
        elif c.p_var_y in ['J', 'dJdV']:
            # Symmetric y limits with respect to y=0
            y_abs_max = max(abs(ys_in_range))
            ax.set_ylim([-y_abs_max, y_abs_max])
            y_lim_txt = '{:.1E}'.format(y_abs_max).replace('E', '\nE')  # 1.23 \n E+4
            # ha: horizontal alignment, va: vertical alignment, transAxes: relative coordinates
            ax.text(0.01, 0.99, y_lim_txt, ha='left', va='top', transform=ax.transAxes)
        elif c.p_var_y in ['R', 'RA']:
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
plt.savefig(save_file_name_base + '.png', dpi=200, transparent=True)
#print('Saving', save_file_name_base + '.pdf')
#plt.savefig(save_file_name_base + '.pdf', transparent=True)  # dpi is ignored, transparent as well?
