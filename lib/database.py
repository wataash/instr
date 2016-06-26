from datetime import datetime
import math

import numpy as np
import pandas.io.sql as psql
import unittest2

import lib.constants as c
from lib.algorithms import calc_coord, fit_R3, is_good_RA
from lib.mysql_handler import MySqlHandler


# TODO class to functions

class Database(MySqlHandler):
    """Does not commit automatically."""
    def _get_device_id(self, sample, mesa, X, Y) -> int or None:
        """Return None if not found."""
        query = ('SELECT device_id FROM v04_device WHERE '
                 'sample=%s AND mesa=%s AND X=%s AND Y=%s')
        ret = self.q_single(query, (sample, mesa, X, Y))
        return ret

    def _get_coord(self, mask, mesa, X, Y) -> list:
        """
        Get various coordinates.
        Return [xs_mesa, ys_mesa, xs_pad, ys_pad, X_pad, Y_pad].
        :return: [xs_mesa, ys_mesa, xs_pad, ys_pad, X_pad, Y_pad]
        """
        query = ('SELECT dX, dY, xm_mesa, ym_mesa, xm_pad, ym_pad '
                 'FROM v02_mesa WHERE mask=%s AND mesa=%s')
        resp = self.q_row_abs(query, (mask, mesa,))
        dX, dY, xm_mesa, ym_mesa, xm_pad, ym_pad = resp
        return calc_coord(X, Y, dX, dY, xm_mesa, ym_mesa, xm_pad, ym_pad)

    def _insert_device(self, sample, mesa, X, Y) -> (int, bool):
        """Return ("device_id", is inserted)"""
        device_id = self._get_device_id(sample, mesa, X, Y)
        if device_id is not None:
            return device_id, False
        q = ('SELECT mask, mesa_id FROM v03_sample_mesa '
             'WHERE sample=%s AND mesa=%s')
        mask, mesa_id = self.q_row_abs(q, (sample, mesa,))

        xs_mesa, ys_mesa, xs_pad, ys_pad, X_pad, Y_pad = \
            self._get_coord(mask, mesa, X, Y)

        oper = ('INSERT INTO device (sample, mesa_id, X, Y, '
                'xs_mesa, ys_mesa, xs_pad, ys_pad, X_pad, Y_pad)'
                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)')
        self.exe(oper, (sample, mesa_id, X, Y,
                        xs_mesa, ys_mesa, xs_pad, ys_pad, X_pad, Y_pad))

        mesa_id = self._get_device_id(sample, mesa, X, Y)
        if mesa_id is None:
            raise RuntimeError('Insertion error.')
        return mesa_id, True

    def _insert_vi_param(
            self, sample, mesa, X, Y, dt, n, comp, V, inst) -> int:
        """Return "VI_param_id"."""
        device_id, _ = self._insert_device(sample, mesa, X, Y)
        oper = ('INSERT INTO VI_param '
                '(device_id, dt, n, comp, V, inst) '
                'VALUES (%s, %s, %s,%s,   %s,%s)')
        self.exe(oper, (device_id, dt, n, comp, V, inst,))
        oper = ('SELECT VI_param_id FROM VI_param '
                'WHERE device_id=%s AND dt=%s')
        vi_param_id = self.q_single(oper, (device_id, dt,))
        return vi_param_id

    def insert_vis(self, sample, mesa, X, Y,
                   dt, n, comp, V, inst, VIs) -> int:
        """
        :param dt: UTC
        :return: vi_param_id
        """
        if isinstance(VIs, np.ndarray):
            VIs = VIs.tolist()
        VI_param_id = \
            self._insert_vi_param(sample, mesa, X, Y, dt, n, comp, V, inst)
        iVIs = [(VI_param_id, V, I) for (V, I) in VIs]
        oper = 'INSERT INTO VI (VI_param_id, V, I) VALUES (%s, %s, %s)'
        self.exem(oper, iVIs)
        return VI_param_id


def calc_tx(x, y, t1, t2, x1a, y1a, x1b, y1b, x2a, y2a, x2b, y2b):
        """
        Read the doc.
        Assuming theta1 != theta2
        yb > ya to get positive value in atan2.

        >>> calc_tx(14, 15, 3.8, 0, 16.5, 100, 16.5, -100, 8, 1, 3, 16)
        (3.053502572324221, 93.62148470411735, 90.0, 108.43494882292202)

        >>> calc_tx(14, 15, 3.8, 0, 16.5, -100, 16.5, 100, 3, 16, 8, 1)
        (3.8851770960079905, 93.62148470411735, 90.0, -71.56505117707799)
        """
        x_inter = -((x1a - x1b)*x2b*y2a - (x1a - x1b)*x2a*y2b - \
                    (x1b*x2a - x1b*x2b)*y1a + (x1a*x2a - x1a*x2b)*y1b) / \
                  ((x2a - x2b)*y1a - (x2a - x2b)*y1b - \
                   (x1a - x1b)*y2a + (x1a - x1b)*y2b)
        y_inter = (((x1b - x2b)*y1a - (x1a - x2b)*y1b)*y2a - \
                   ((x1b - x2a)*y1a - (x1a - x2a)*y1b)*y2b) / \
                  ((x2a - x2b)*y1a - (x2a - x2b)*y1b - \
                   (x1a - x1b)*y2a + (x1a - x1b)*y2b)
        theta1 = math.atan2(y1b - y1a, x1b - x1a) if x1a != x1b else math.pi/2
        theta2 = math.atan2(y2b - y2a, x2b - x2a) if x2a != x2b else math.pi/2
        theta = math.atan2(y - y_inter, x - x_inter)
        t = t1 + ((t2-t1)/(theta2-theta1))*(theta-theta1)
        return t, theta*180/math.pi, theta1*180/math.pi, theta2*180/math.pi


def update_fit_R3(db_read, db_rds, sample, mesa='%', commit=False):
    """
    :type db_read: Database
    :type X: int or str
    :type Y: int or str
    """
    q = ('SELECT device_id, mesa, X, Y, area FROM v04_device '
         'WHERE sample=%s AND mesa LIKE %s')
    params = db_rds.q_all(q, (sample, mesa,))
    for devid, mesa, X, Y, area in params:
        print('update_fit_R3: devid{} {} {} X{} Y{} querying...'.
              format(devid, sample, mesa, X, Y), end=' ', flush=True)
        q = 'SELECT V, I FROM v_py_fitR3 WHERE device_id=%s'
        vis = db_read.pdq(q, (devid,))
        vis_100meV = vis[(-0.1 <= vis.V) & (vis.V <= 0.1)]
        if vis_100meV.empty:
            print('VIs (100meV) empty. skip.')
            continue
        c1, _, _, _ = fit_R3(vis_100meV)
        _, _, _, R2 = fit_R3(vis)
        R0 = 1/c1
        RA0 = area/c1
        oper = ('UPDATE device SET suss_R0=%s, suss_RA0=%s, suss_R2=%s '
                'WHERE device_id=%s')
        db_rds.cursor.execute(oper, (R0, RA0, R2, devid,))
        if commit:
            db_rds.cnx.commit()
        print('Updated.')


def update_coords(db_rds, sample, commit=False):
    oper = ('SELECT X, Y, dX, dY, xm_mesa, ym_mesa, xm_pad, ym_pad, '
            'device_id '
            'FROM v04_device WHERE sample=%s')
    db_rds.exe(oper, (sample,))
    dev_params = db_rds.fetchall()
    data = []
    for p in dev_params:
        X_pad, Y_pad, X_mesa, Y_mesa = calc_coord(*p[:8])
        device_id = p[8]
        data.append([X_pad, Y_pad, X_mesa, Y_mesa, sample, device_id])

    oper = ('UPDATE device '
            'SET X_pad=%s, Y_pad=%s, X_mesa=%s, Y_mesa=%s '
            'WHERE sample=%s AND device_id=%s')
    print('update_coords: updating...')
    db_rds.exem(oper, data)
    if commit:
        db_rds.cnx.commit()
    print('Done.')


def update_tx_rotating(db_rds, sample, commit=False):
    if sample == 'dummy_sample1':
         t1, t2 = 2.6367, 0
         x1a, y1a, x1b, y1b = 14.5, 8.5, 13.5, 15.5
         x2a, y2a, x2b, y2b = 7.5, 2.5, 3.5, 15.5
    else:
        raise ValueError
    print(0)
    sql = ('SELECT device_id, X_mesa, Y_mesa FROM v04_device WHERE sample=%s')
    df = db_rds.pdq(sql, (sample,))
    print(1)
    df['tx'] = df.apply(lambda x: calc_tx(x.X_mesa, x.Y_mesa, t1, t2, x1a, y1a,
                                          x1b, y1b, x2a, y2a, x2b, y2b)[0],
                        axis=1)
    sql = 'UPDATE device SET tX=%s WHERE device_id=%s'
    tis = df[['tx', 'device_id']].values.tolist()
    tis = [[t, int(i)] for t, i in tis]
    print('Updating...')
    db_rds.exem(sql, tis)
    print('Done.')
    if commit:
        db_rds.cnx.commit()


class TestDatabase(unittest2.TestCase):
    def setUp(self):
        self.db = Database(**c.mysql_config)
        self.mask = 'dummy_mask'
        self.mesa = 'dummy_mesa'
        self.sample = 'dummy_sample'

    def test_20_get_device_id(self):
        device_id = self.db._get_device_id(self.sample, self.mesa, 1, 1)
        self.assertIsInstance(device_id, int)
        self.assertEqual(
                self.db._get_device_id('Not exist sample',
                                       self.mesa, 1, 1), None)

    def test_30_get_calc_coord(self):
        # [xs_mesa, ys_mesa, xs_pad, ys_pad, X_pad, Y_pad]
        resp = self.db._get_coord('dummy_mask', 'dummy_mesa_right', 1, 1)
        self.assertEqual(resp, [200, 5, 200, 0, 1.2, 1])

        with self.assertRaises(RuntimeError):
            self.db._get_coord('not exist mask', 'not exist mesa', 1, 1)

        with self.assertRaises(RuntimeError):
            self.db._get_coord('dummy_mask', 'not exist mesa', 1, 1)

    def test_40_insert_device(self):
        device_id, is_inserted = \
            self.db._insert_device(self.sample, self.mesa, 1, 1)
        self.assertIsInstance(device_id, int)
        self.assertEqual(is_inserted, False)

        # DO NOT commit.
        # Insertion will be effective while only running the process.
        device_id, is_inserted = \
            self.db._insert_device(self.sample, self.mesa, 999, 999)
        self.assertIsInstance(device_id, int)
        self.assertEqual(is_inserted, True)

        device_id_999, is_inserted = \
            self.db._insert_device(self.sample, self.mesa, 999, 999)
        self.assertEqual(device_id, device_id_999)
        self.assertEqual(is_inserted, False)

    def test_60_insert_VI_param(self):
        TestDatabase.now = datetime.utcnow().replace(microsecond=0)
        vi_param_id = \
            self.db._insert_vi_param(self.sample, self.mesa, 1, 1,
                                     TestDatabase.now, 3, 0, 0.2, 'test inst')
        q = 'SELECT * FROM v05_VI_param WHERE VI_param_id=%s'
        resp = self.db.q_row_abs(q, (vi_param_id,))
        print(resp)

    def test_70_insert_VIs(self):
        # noinspection PyUnresolvedReferences
        vi_param_id = \
            self.db.insert_vis(
                    self.sample, self.mesa, 1, 1, TestDatabase.now, 3, 0, 0.2,
                    'test inst', [(0, 0), (0.1, 1e-3), (0.2, 2e-3)])
        q = 'SELECT * FROM v05_VI_param WHERE VI_param_id=%s'
        par = self.db.q_row(q, (vi_param_id,))
        print(par)
        q = 'SELECT * FROM VI where VI_param_id=%s'
        vis = self.db.q_all(q, (vi_param_id,))
        print(vis)


if __name__ == "__main__":
    # Carefully commit in evaluator!

    # unittest2.main()  # DO NOT commit.
    sample = 'dummy_sample'
    db = Database(**c.mysql_config)
    db_read = Database(user='readonly', database='master_db')

    # update_coords(db, sample, commit=True)
    # update_tx_rotating(db, sample, True)

    update_fit_R3(db_read, db, sample, mesa='%', commit=True)
