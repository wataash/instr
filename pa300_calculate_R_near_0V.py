"""
Make table "resistance" if not exist.

CREATE TABLE `resistance` (
	`sample`	TEXT,
	`mesa`	TEXT,
	`X`	INTEGER,
	`Y`	INTEGER,
	`V`	REAL,
	`samples`	INTEGER,
	`R`	REAL,
	`R2`	REAL,
	`R95_lo`	REAL,
	`R95_hi`	REAL
);
"""

# Std libs
import math
import os
import sqlite3
# Non-std libs
import numpy as np
import statsmodels.api as sm



sample = 'E0339 X9-12 Y13-16'
mesa = ['D169', 'D56.3', 'D16.7', 'D5.54'][1]
dia = {'D169': 169e-6, 'D56.3': 56.3e-6, 'D16.7': 16.7e-6, 'D5.54': 5.54e-6}[mesa] # diameter [m]
area = math.pi * (dia/2)**2  # [m^2]
min_X, max_X, min_Y, max_Y = (1, 17, 1, 17)
volt = 0.010  # Samples (V,I)s from (-volt to +volt)
sqlite3_file_path = os.path.expanduser('~') + r'\Documents\instr_data/IV.sqlite3'

sqlite3_connection = sqlite3.connect(sqlite3_file_path)
cursor_t0 = sqlite3_connection.cursor()
cursor = sqlite3_connection.cursor()

for Y in range(min_Y, max_Y + 1):
    for X in range(min_X, max_X + 1):
        print(mesa, X,Y)
        VIs = []
        for t0 in cursor_t0.execute('''
                SELECT t0 FROM parameters
                WHERE sample=? AND mesa=? AND X=? AND Y=?
                ''', (sample, mesa, X, Y)):
            VIs += cursor.execute('''
                SELECT V, I FROM IV WHERE t0=?
                AND V BETWEEN -0.010 AND 0.010''',
                t0).fetchall()
        if VIs == []:
            continue
        [V, I] = list(zip(*VIs))
        model = sm.OLS(I, V)
        # c: conductance [S], r: resistance [ohm]
        results = model.fit()
        n = int(results.nobs)  # Number of (V, I) samples
        R = 1/results.params[0]
        RA = R * area  # ohm m2
        # r_stderr = 1/results.bse[0]  # This is wrong
        r95_hi, r95_lo = 1/results.conf_int()[0]  # 95% confident interval
        R2 = results.rsquared
        print(mesa, X, Y)
        cursor.execute('INSERT INTO resistance(sample,mesa,X,Y,V,samples,R,RA,R2,R95_lo,R95_hi) \
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                       (sample, mesa, X, Y, volt, n, R, RA, R2, r95_lo, r95_hi))
        sqlite3_connection.commit()

cursor.close()
cursor_t0.close()
