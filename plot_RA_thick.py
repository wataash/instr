import os
import sqlite3

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

sample = 'E0339'
#mesa = 'D56.3'
sqlite3_file_path = os.path.expanduser('~') + r'\Documents\instr_data/IV.sqlite3'


sqlite3_connection = sqlite3.connect(sqlite3_file_path)
cursor = sqlite3_connection.cursor()

tmp = cursor.execute('''
        SELECT Y, R FROM resistance
        WHERE sample=? AND mesa=?
        ''', (sample, 'D169')).fetchall()
Ys, Rs = np.array(tmp).transpose()
t_MgO = (Ys-1) * 5/(17-1)

tmp = cursor.execute('''
        SELECT Y, R FROM resistance
        WHERE sample=? AND mesa=?
        ''', (sample, 'D56.3')).fetchall()
Ys2, Rs2 = np.array(tmp).transpose()
t_MgO2 = (Ys2-1) * 5.4/(17-1)

font = {'size': 18}
matplotlib.rc('font', **font)

plt.figure(facecolor='w')

#plt.semilogy(Ys, Rs, 'o')
#plt.semilogy(Ys2, Rs2, 'o')
#plt.xlabel('Y')

plt.semilogy(t_MgO, Rs, 'o')
plt.semilogy(t_MgO2, Rs2, 'o')
plt.xlabel('MgO thickness')

plt.ylabel('Resistance $(\\Omega)$')
plt.legend(['$\\phi$169um','$\\phi$56.3um'], loc=2)

plt.show()


#plt.ylim([10e3, 10e9])
# TODO: xlabel, ylabel,  error bar

print(0)
