# Old data format!

from collections import defaultdict
import os
# import sqlite3
import matplotlib.pyplot as plt
import numpy as np

# Prefix 'd': dictionary

data_dir = os.environ['appdata'] + r'\Instr\Agilent4156C'
# conn = sqlite3.connect(data_dir + '\\' + 'data.db')
d_t = defaultdict(list)  # Time
d_I = defaultdict(list)  # Current
d_R = defaultdict(list)  # Resistance
for fname in [fname_all for fname_all in os.listdir(data_dir) if fname_all.startswith('ContactTest_2015071')]:
    with open(data_dir + '\\' + fname) as f:
        tmp = f.name.split('_')
        X = int(tmp[3][1:])
        Y = int(tmp[4][1:])
        D = float(tmp[5][1:])
        V = float(tmp[6].split('V')[0])  # '0.1V.csv' -> 0.1
        read = f.read().split()
        newt = [float(t) for t in read[0].split(',')]
        newI = [float(I) for I in read[1].split(',')]
        newR = [V/I for I in newI if I != 0]
        d_t[(X, Y, D, V)].append(newt)
        d_I[(X, Y, D, V)].append(newI)
        d_R[(X, Y, D, V)] += newR

d_R_ave = {}
for XYDv, value in d_R.items():
    d_R_ave[XYDv] = np.mean(value)

voltage = 1e-3
dia = 56.3
f, axarr = plt.subplots(4, 10, sharex=True)
f.patch.set_alpha(0.)
# X2Y4 X3Y4 ... X11Y4
# X2Y3 X3Y3 ...
# X2Y2 X3Y2 ...
# X2Y1 X3Y1 ... X11Y1
# plt.title('E0326-2-1 (D 5.54um, X 2-11, Y 1-4) I(A) vs t(s)')
for (rowi, coli) in [(rowi, coli) for rowi in range(4) for coli in range(10)]:
    xi = coli + 2
    yi = 4 - rowi
    for (t, I) in zip(d_t[(xi, yi, dia, voltage)], d_I[(xi, yi, dia, voltage)]):
        try:
            axarr[rowi, coli].semilogy(t, I)
        except Exception:
            print('negative value on rowi:{} coli:{} xi:{} yi:{}'.format(rowi, coli, xi, yi))
# f.subplots_adjust(hspace=0)
f.subplots_adjust(wspace=0)
# f.subplots_adjust(0,0)
# plt.setp([a.get_xticklabels() for a in f.axes[:-1]], visible=False)
plt.show()
print(0)



# +1mV
fig = plt.figure()
fig.patch.set_alpha(0.)
ax = plt.gca()
ax.set_yscale('log')
plt.title('E0326-2-1 (X=1: Fe 0nm, X=10: 5.45nm)')
plt.xlabel('X')
plt.ylabel('Resistance at 1mV')
for (area, color_) in zip([5.54, 16.7, 56.3], ('r', 'g', 'b')):
    for (XYDv, R_ave) in [(XYDv, R_ave) for (XYDv, R_ave) in d_R_ave.items() if XYDv[2] == area and XYDv[3] == 1e-3 and R_ave > 0]:
        ax.scatter(XYDv[0], R_ave, color=color_)
plt.show()

# -1mV
fig = plt.figure()
fig.patch.set_alpha(0.)
ax = plt.gca()
ax.set_yscale('log')
plt.title('E0326-2-1 (X=1: Fe 0nm, X=10: 5.45nm)')
plt.xlabel('X')
plt.ylabel('Resistance at -1mV')
for (area, color_) in zip([5.54, 16.7, 56.3], ('r', 'g', 'b')):
    for (XYDv, R_ave) in [(XYDv, R_ave) for (XYDv, R_ave) in d_R_ave.items() if XYDv[2] == area and XYDv[3] == -1e-3 and R_ave > 0]:
        ax.scatter(XYDv[0], R_ave, color=color_)
plt.show()

for (XYDv, R_ave) in [(XYDv, R_ave) for (XYDv, R_ave) in d_R_ave.items() if R_ave <= 0]:
    print('Resistance{0}: {1}'.format(XYDv, R_ave))

print(1)
