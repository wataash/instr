# Std libs
import json
import os.path
import sqlite3
# Non-std libs
import matplotlib.pyplot as plt
# My libs
import constants as c

conn_params = sqlite3.connect(c.sql_params_dropbox)
cur_params = conn_params.cursor()

Xs = {}
Ys = {}
Rs = {}
c.p_mesas = c.p_mesas[3:4]

fig = plt.figure()
ax = plt.gca()
ax.set_yscale('log')

#for mesa in c.p_mesas:
#    XYRs = cur_params.execute(
#        'SELECT X,Y,R FROM resistance WHERE sample=? AND mesa=? AND Y>=1',
#        (c.p_sample, mesa)).fetchall()
#    if XYRs == []:
#        continue
#    Xs[mesa], Ys[mesa], Rs[mesa] = zip(*XYRs)
#    ax.scatter(Xs[mesa], Rs[mesa], c=Ys[mesa], marker='x', label=mesa)
#    for i in range(len(Xs[mesa])):
#        ax.annotate(Ys[mesa][i], (Xs[mesa][i], Rs[mesa][i]))
#    ax.legend(loc=2)
#    #plt.ylim([1e3, 1e8])

for mesa in c.p_mesas:
    XYRs = cur_params.execute(
        'SELECT X,Y,RA FROM resistance WHERE sample=? AND mesa=? AND Y>=10',
        (c.p_sample, mesa)).fetchall()
    if XYRs == []:
        continue
    Xs[mesa], Ys[mesa], Rs[mesa] = zip(*XYRs)
    ax.scatter(Xs[mesa], Rs[mesa], marker='o', label=mesa)

    XYRs = cur_params.execute(
        'SELECT X,Y,RA FROM resistance WHERE sample=? AND mesa=? AND Y<=9',
        (c.p_sample, mesa)).fetchall()
    if XYRs == []:
        continue
    Xs[mesa], Ys[mesa], Rs[mesa] = zip(*XYRs)
    ax.scatter(Xs[mesa], Rs[mesa], marker='o', c='r', label=mesa)

plt.show()

conn_params.close()
