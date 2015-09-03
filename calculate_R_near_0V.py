import json
#import math
#import os
import sqlite3

#import matplotlib.pyplot as plt
import numpy as np
#import statsmodels.api as sm

sample = 'E0339'
sqlite3_file_path = r'C:\Users\wsh14\Documents\instr_data/IV.sqlite3'

sqlite3_connection = sqlite3.connect(sqlite3_file_path)
cursor_t0 = sqlite3_connection.cursor()
cursor_IV = sqlite3_connection.cursor()

for Y in range(1, 17 + 1):
    for X in range(1, 17 + 1):
        VIs = np.array([[]])
        for t0 in cursor_t0.execute('''
                SELECT t0 FROM parameters
                WHERE sample=? AND X=? AND Y=? AND
                t0 BETWEEN 20150826130701 AND 20150826131040
                ''', (sample, X, Y)):
            tmp = cursor_IV.execute('SELECT V, I FROM IV WHERE t0=?', t0).fetchall()
            #VIs += tmp
            VIs = np.append(VIs, tmp)

#for t0 in cursor_t0.execute('SELECT t0 FROM parameters'):
#    print(t0)
#    tmp = cursor_IV.execute('''
#        SELECT V, I FROM IV
#        WHERE t0=? AND V BETWEEN -0.010 AND 0.010
#        ''', t0).fetchall()
#    VIs = np.array(tmp)

#    V = VIs.transpose()[0]
#    I = VIs.transpose()[1]


#    model = sm.OLS(I, V)
#    results = model.fit()

#    tmp = np.polyfit(V, I, 1)
#    print(tmp)

#    sm.add_constant(