from collections import defaultdict
import os
# import sqlite3
import matplotlib.pyplot as plt
import numpy as np

# Prefix 'd': dictionary

sample = 'E0326-2-1'
dia = 169
data_dir = os.environ['appdata'] + r'\Instr\Agilent4156C'
good_XYs = [(6,1), (7,1), (8,1), (10,1), (11,1),
            (7,2), (8,2), (9,2), (10,2),
            (2,3), (3,3), (8,3), (9,3), (10,3), (11,3),
            (7,4), (8,4), (9,4),]
good_XYs_str = ['X{}_Y{}'.format(X, Y) for (X, Y) in good_XYs]
d_V = defaultdict(list)  # Voltage
d_I = defaultdict(list)  # Current
d_R = defaultdict(list)  # Resistance
for fname in [fname_all for fname_all in os.listdir(data_dir) if
              fname_all.startswith('double-sweep') and
              'D{}'.format(dia) in fname_all and
              sample in fname_all and
              any(XY in fname_all for XY in good_XYs_str)]:
    with open(data_dir + '\\' + fname) as f:
        tmp = f.name.split('_')
        X = int(tmp[3][1:])
        Y = int(tmp[4][1:])
        D = float(tmp[5][1:])
        read = f.read().split()
        newV = [float(t) for t in read[0].split(',')]
        newI = [float(I) for I in read[1].split(',')]
        newR = [(V/I if abs(V) > 0.010 else None) for (V, I) in zip(newV, newI)]
        d_V[(X, Y, D)] += newV
        d_I[(X, Y, D)] += newI
        d_R[(X, Y, D)] += newR
        print(X, Y, D)


Xmin = 1
Xmax = 11
Ymin = 1
Ymax = 4

numX = Xmax - Xmin + 1
numY = Ymax - Ymin + 1
f, axarr = plt.subplots(numY, numX, figsize=(numX, numY), facecolor='w')
f.subplots_adjust(top=1, bottom=0, left=0, right=1, wspace=0, hspace=0)
# f.text(0.5, 0.95, 'E0326-2-1 (D:{}um, X:{}-{}, Y:{}-{}, I(A) vs V(V)'.format(dia, Xmin, Xmax, Ymin, Ymax),
#                horizontalalignment='center')
for (rowi, coli) in [(rowi, coli) for rowi in range(numY) for coli in range(numX)]:
    print(rowi, coli)
    # (rowi, coli) X, Y
    # (00)XminYmax ...              (09)XmaxYmax
    # ...
    # (08)Xmin(Ymin+1) ...
    # (09)XminYmin 19(Xmin+1)Ymin ... (99)XmaxYmin
    X = coli + Xmin
    Y = Ymax - rowi
    p = axarr[rowi, coli].plot(d_V[(X, Y, dia)], d_R[(X, Y, dia)], 'b')  # d_I or d_R
    axarr[rowi, coli].set_xticks([])
    axarr[rowi, coli].set_yticks([])
    axarr[rowi, coli].set_xlim([-0.5, 0.5])
# plt.show()
plt.savefig(os.path.expanduser('~') + r'\Desktop\tmp.png', dpi=300, transparent=True)

print(0)
