import math
import os
import sqlite3

from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt
#import numpy as np


# Configurations ---------------------------------------------------------------
#sqlite3_file = os.path.expanduser('~') + '/Documents/instr_data/IV.sqlite3'

# Device data
#sample = 'E0339 X9-12 Y13-16'
#mesa = ['D169', 'D56.3', 'D16.7', 'D5.54'][0]
#var_y = ['R', 'RA'][0]
#c_min = {'R': 100, 'RA': 1e-10}[var_y]
#c_max = {'R': 1e9, 'RA': 1e-5}[var_y]
#min_X, max_X, min_Y, max_Y = (1, 17, 1, 17)


# Calculations -----------------------------------------------------------------
png_file_name = os.path.expanduser('~')
# E0339_D169_R-XY.png
png_file_name += '/Desktop/{sample}_{mesa}_R-XY.png'.format(sample=sample, mesa=mesa)
print('Save to:', png_file_name)

# Connect to database
#sqlite3_connection = sqlite3.connect(sqlite3_file)
#cursor = sqlite3_connection.cursor()


# Plot -------------------------------------------------------------------------
XYRs = cursor.execute('SELECT X,Y,R FROM resistance WHERE sample=? AND mesa=?', (sample, mesa)).fetchall()

# /300: inches to px (for 300dpi)
# 1000px w/ colorbar, 3200px w/o
fig = plt.figure(figsize=(3200/300,3200/300))  
ax = fig.add_subplot(1,1,1)

# Ticks and grid
ax.grid(which='minor', linestyle='-', color='gray')
ax.set_xticks(list(range(min_X, max_X+1)))
ax.set_xticks([x + 0.5 for x in range(min_X, max_X)], minor=True)  # (min1,max9) -> 1.5, 2.5, ..., 8.5
ax.set_yticks(list(range(min_Y, max_Y+1)))
ax.set_yticks([x + 0.5 for x in range(min_Y, max_Y)], minor=True)  # (min1,max9) -> 1.5, 2.5, ..., 8.5

# Axes
plt.xlim([min_X - 0.6, max_X + 0.6])
plt.ylim([min_Y - 0.5, max_Y + 0.5])
ax.tick_params(labeltop=True, labelright=True)

# Plot
Xs = []
Ys = []
Rs = []
for (X, Y, R) in XYRs:
    if R is None:
        continue
    Xs.append(X)
    Ys.append(Y)
    Rs.append(R)
    txt = '{:.2E}'.format(R).replace('E', '\nE')  # 1.2 \n E+03
    ax.annotate(txt, xy=(X,Y), verticalalignment='center', horizontalalignment='center')

# vmin, vmax: color scale
sc = ax.scatter(Xs, Ys, c=Rs, cmap='coolwarm', s=1200, marker='s', norm=LogNorm(), vmin=c_min, vmax=c_max)

#plt.colorbar(sc)

plt.savefig(png_file_name, transparent=True, dpi=300)
