# Std libs
import math
import os
import sqlite3
# Non-std libs
import numpy as np
import statsmodels.api as sm
# My libs
import constants as c

volt = 0.020  # voltage interval to fit

conn_params = sqlite3.connect(c.sql_params_local)
conn_IVs = sqlite3.connect(c.dropbox_dir + 'IVs_' + c.p_sample + '.sqlite3')
cur_params = conn_params.cursor()
cur_IVs = conn_IVs.cursor()

mask, X_min, X_max, Y_min, Y_max = \
    cur_params.execute('SELECT mask, X_min, X_max, Y_min, Y_max \
                        FROM samples WHERE sample=?',
                       (c.p_sample,)
                      ).fetchone()

mesa_area_pairs = \
    cur_params.execute('SELECT mesa, area FROM mesas WHERE mask=?',
                       (mask,)).fetchall()

olds = {}  # old and
news = {}  # new fitting results
for (mesa, area) in mesa_area_pairs:
    for Y in range(Y_min, Y_max + 1):
        for X in range(X_min, X_max + 1):
            print('\nProcessing', mesa, X, Y, end='.  ')
            dat = cur_params.execute(
                'SELECT V, samples, R, RA, R2, R95_lo, R95_hi FROM resistance \
                 WHERE sample=? AND mesa=? AND X=? AND Y=?',
                (c.p_sample, mesa, X, Y)).fetchall()
            if len(dat) >= 2:
                raise RuntimeError('Detected duplication in resistance table.')
            elif len(dat) == 1:
                tmp = dat[0]
                olds = {'V': tmp[0], 'samples': tmp[1],
                        'R': tmp[2], 'RA': tmp[3],
                        'R2': tmp[4], 'R95_lo': tmp[5], 'R95_hi': tmp[6], }
                                
            VIs = []
            for t0 in cur_params.execute(
                    'SELECT t0 FROM IV_params \
                     WHERE sample=? AND mesa=? AND X=? AND Y=?',
                    (c.p_sample, mesa, X, Y)):
                VIs += cur_IVs.execute(
                    'SELECT V, I FROM IVs \
                     WHERE t0=? AND V BETWEEN -? AND ?',
                    (t0[0], volt, volt,)).fetchall()
            if VIs == []:
                print('IV not found. Skip.')
                continue
            [V, I] = list(zip(*VIs))

            # c: conductance [S], r: resistance [ohm]
            model = sm.OLS(I, V)
            results = model.fit()
            news['V'] = volt
            news['samples'] = int(results.nobs)  # Number of (V, I) samples
            news['R'] = 1/results.params[0]
            news['RA'] = news['R'] * area  # ohm m2
            # 95% confident interval
            # r_stderr = 1/results.bse[0] is mathematically wrong
            news['R95_hi'], news['R95_lo'] = 1/results.conf_int()[0]
            news['R2'] = results.rsquared
            if olds != {}:
                for var in ['R', 'RA', 'R95_hi', 'R95_lo', 'R2']:
                    # 0.01% of error tolerance
                    if 0.9999 < olds[var]/news[var] < 1.0001:
                        news[var] = olds[var]
                if olds == news:
                    print('Fitting result was not changed.')
                    continue
                else:
                    print('Update data. old and new:\n', olds, '\n', news)
                    olds = {}
                    cur_params.execute(
                        'UPDATE resistance set \
                         V=?,samples=?,R=?,RA=?,R2=?,R95_lo=?,R95_hi=? \
                         WHERE sample=? AND mesa=? AND X=? AND Y=?',
                        (volt, news['samples'], news['R'], news['RA'],
                         news['R2'], news['R95_lo'], news['R95_hi'],
                         c.p_sample, mesa, X, Y))
            else:
                print('Writing new data.')
                cur_params.execute(
                    'INSERT INTO \
                     resistance(sample,mesa,X,Y,V,samples,R,RA,R2,R95_lo,R95_hi) \
                     VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                    (c.p_sample, mesa, X, Y, volt,
                     news['samples'], news['R'], news['RA'],
                     news['R2'], news['R95_lo'], news['R95_hi']))
            conn_params.commit()

cur_params.close()
cur_IVs.close()
