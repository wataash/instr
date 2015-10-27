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
        x_mesa = (X-1)*dX + xm_mesa
        y_mesa = (Y-1)*dY + ym_mesa
        x_pad = (X-1)*dX + xm_pad
        y_pad = (Y-1)*dY + ym_pad
        print(mask, mesa, X, Y)
        cur_params.execute('''INSERT OR REPLACE INTO
                              coord(mask, mesa, X, Y, xmesa, ymesa, xpad, ypad)
                              VALUES(?,   ?,    ?, ?, ?,     ?,     ?,    ?)''',
                           (mask, mesa, X, Y, 
                            x_mesa, y_mesa, x_pad, y_pad,))
conn_params.commit()
