# Std libs
from itertools import product
import sqlite3
# My libs
import constants as c

conn_params = sqlite3.connect(c.sql_params_dropbox)
cur_params = conn_params.cursor()

dats = cur_params.execute('''SELECT mask, mesa, xm_mesa, ym_mesa, xm_pad, ym_pad
                             FROM mesas''').fetchall()

for dat in dats:
    mask, mesa, xm_mesa, ym_mesa, xm_pad, ym_pad = dat
    dX, dY = cur_params.execute('SELECT d_X, d_Y FROM masks WHERE mask=?',\
                                (mask,)).fetchone()
    for (X, Y) in product(range(1,21), range(1,21)):
        xs_mesa = (X-1)*dX + xm_mesa
        ys_mesa = (Y-1)*dY + ym_mesa
        xs_pad = (X-1)*dX + xm_pad
        ys_pad = (Y-1)*dY + ym_pad
        X_pad = X + xm_pad/dX
        Y_pad = Y + ym_pad/dY
        print(mask, mesa, X, Y)
        cur_params.execute('''
            INSERT OR REPLACE INTO
            coord(mask, mesa, X, Y,
                  xs_mesa, ys_mesa, xs_pad, ys_pad, X_pad, Y_pad)
            VALUES(?,?,?,?,?,?,?,?,?,?)''',
            (mask, mesa, X, Y, xs_mesa, ys_mesa, xs_pad, ys_pad, X_pad, Y_pad))
conn_params.commit()
