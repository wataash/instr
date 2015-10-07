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
import json
import math
import os
import sqlite3
# Non-std libs
import numpy as np
import statsmodels.api as sm

# TODO: update if exists
# for sample, mesa, X, Y in "parameters"
# update if samples on "parameters" != samples on "resistancee"

with open(os.path.expanduser('~') + '/Dropbox/master-db/src-master-db/pa300_config.json') as f:
    j = json.load(f)

sample = j['calR_sample']

conn_params = sqlite3.connect(j['db_params_file'].replace('home', os.path.expanduser('~')))
conn_IVs = sqlite3.connect(j['pltRX_db_IVs_file'].replace('home', os.path.expanduser('~')))
cur_params = conn_params.cursor()
cur_IVs = conn_IVs.cursor()

#j['calR_sample'] = 'E0326-2-1'
#mesa = ['D169', 'D56.3', 'D16.7', 'D5.54'][1]
#dia = {'D169': 169e-6, 'D56.3': 56.3e-6, 'D16.7': 16.7e-6, 'D5.54': 5.54e-6}[mesa] # diameter [m]
#area = math.pi * (dia/2)**2  # [m^2]
#min_X, max_X, min_Y, max_Y = (1, 17, 1, 17)

mask, X_min, X_max, Y_min, Y_max = \
    cur_params.execute('SELECT mask, X_min, X_max, Y_min, Y_max \
                        FROM samples WHERE sample=?',
                       (sample,)
                      ).fetchone()

mesa_areas = cur_params.execute('SELECT name, area FROM mesas WHERE mask=?', (mask,)).fetchall()
#mesas = [mesa[0] for mesa in mesas]

for (mesa, area) in mesa_areas:
    for Y in range(Y_min, Y_max + 1):
        for X in range(X_min, X_max + 1):
            print('Processing', mesa, X, Y)
            dat = cur_params.execute('''SELECT * FROM resistance
                WHERE sample=? AND mesa=? AND X=? AND Y=?''',
                (sample, mesa, X, Y)).fetchall()
            if dat != []:
                # TODO: recalculate
                print('Skip')
                continue
                                
            VIs = []
            for t0 in cur_params.execute('''
                    SELECT t0 FROM IV_params
                    WHERE sample=? AND mesa=? AND X=? AND Y=?
                    ''', (sample, mesa, X, Y)):
                VIs += cur_IVs.execute('''
                    SELECT V, I FROM IVs WHERE t0=?
                    AND V BETWEEN -0.010 AND 0.010''',
                    t0).fetchall()
            if VIs == []:
                print('nodata. skip.')
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
            print('Writing', mesa, X, Y)
            cur_params.execute('INSERT INTO resistance(sample,mesa,X,Y,V,samples,R,RA,R2,R95_lo,R95_hi) \
                                VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                               (j['calR_sample'], mesa, X, Y, j['calR_volt'], n, R, RA, R2, r95_lo, r95_hi))
            conn_params.commit()

cur_params.close()
cur_IVs.close()
