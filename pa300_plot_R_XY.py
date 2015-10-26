# Std libs
import math
import os
import sqlite3
# Non-std libs
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt
# MyLibs
import constants as c


var_z = ['R', 'RA'][1]
auto_color = False
c_min = {'R': 1e3, 'RA': 1e-8}[var_z]
c_max = {'R': 1e5, 'RA': 1e-3}[var_z]


conn_params = sqlite3.connect(c.sql_params_dropbox)
cur_params = conn_params.cursor()

mask, X_min, X_max, Y_min, Y_max = \
    cur_params.execute('SELECT mask, X_min, X_max, Y_min, Y_max\
                        FROM samples WHERE sample=?',
                        (c.p_sample,)).fetchone()


# Plot -------------------------------------------------------------------------
mesas = cur_params.execute('SELECT mesa FROM mesas WHERE mask=?', (mask,)). \
                              fetchall()
mesas = [x[0] for x in mesas]
for mesa in mesas:
    XYzs = cur_params.execute(
               'SELECT X,Y,z FROM resistance WHERE sample=? AND mesa=?'.
               replace('Y,z', 'Y,' + var_z),
               (c.p_sample, mesa)
           ).fetchall()

    # /100: inches to px (for 100dpi)
    # optimized size
    # X  Y  widt heig
    # 17 8  1100 500
    # 15 4  970  250
    # 4  1  270  300?
    # 4  8  270  500
    fig = plt.figure(figsize=((1100)/100, (500)/100))
    ax = fig.add_subplot(1,1,1)

    # Ticks and grid
    ax.grid(which='minor', linestyle='-', color='gray')
    ax.set_xticks(list(range(X_min, X_max+1)))
    # (min1,max9) -> 1.5, 2.5, ..., 8.5
    ax.set_xticks([x + 0.5 for x in range(X_min, X_max)], minor=True)
    ax.set_yticks(list(range(Y_min, Y_max+1)))
    # (min1,max9) -> 1.5, 2.5, ..., 8.5
    ax.set_yticks([x + 0.5 for x in range(Y_min, Y_max)], minor=True)

    # Axes
    plt.xlim([X_min - 0.6, X_max + 0.6])
    plt.ylim([Y_min - 0.5, Y_max + 0.5])
    ax.tick_params(labeltop=True, labelright=True)

    # Plot
    Xs = []
    Ys = []
    zs = []
    for (X, Y, z) in XYzs:
        if z is None:
            continue
        Xs.append(X)
        Ys.append(Y)
        zs.append(z)
        txt = '{:.2E}'.format(z).replace('E', '\nE')  # 1.2 \n E+03
        ax.annotate(txt, xy=(X,Y),
                    verticalalignment='center', horizontalalignment='center')

    if auto_color:
        sc = ax.scatter(
            Xs, Ys, c=zs, cmap='coolwarm', s=1200, marker='s', norm=LogNorm())
    else:
        sc = ax.scatter(
            Xs, Ys, c=zs, cmap='coolwarm', s=1200, marker='s', norm=LogNorm(),
            vmin=c_min, vmax=c_max)  # vmin, vmax: color scale
    #plt.colorbar(sc)

    file_name = os.path.expanduser(
        '~/Desktop/{sample}_{mesa}_{var_y}-XY_auto.png'.
        format(sample=c.p_sample, mesa=mesa, var_y=var_z))
    if not auto_color:
        file_name = file_name.replace('auto',
                                      '{c_min:.0E}_{c_max:1.0E}'.
                                      format(c_min=c_min, c_max=c_max))
    plt.savefig(file_name, transparent=True, dpi=100)
