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

import json
import os
import sqlite3

import numpy as np
import statsmodels.api as sm

sample = 'E0339'
mesa = 'D56.3'
volt = 0.010  # Samples (V,I)s from (-volt to +volt)
sqlite3_file_path = os.path.expanduser('~') + r'\Documents\instr_data/IV.sqlite3'

sqlite3_connection = sqlite3.connect(sqlite3_file_path)
cursor_t0 = sqlite3_connection.cursor()
cursor = sqlite3_connection.cursor()

for Y in range(1, 17 + 1):
    for X in range(1, 17 + 1):
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
        r = 1/results.params[0]
        # r_stderr = 1/results.bse[0]  # This is wrong
        r95_hi, r95_lo = 1/results.conf_int()[0]  # 95% confident interval
        R2 = results.rsquared
        print(mesa, X, Y)
        cursor.execute('''
            INSERT INTO resistance(sample,mesa,X,Y,V,samples,R,R2,R95_lo,R95_hi)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ''', (sample, mesa, X, Y, volt, n, r, R2, r95_lo, r95_hi))
        sqlite3_connection.commit()

cursor.close()
cursor_t0.close()
