from datetime import datetime, timedelta

import mysql.connector
import pandas.io.sql as psql
import unittest2


class MySqlHandler:
    def __init__(self, **config):
        self.cnx = mysql.connector.connect(**config)
        self.cursor = self.cnx.cursor()
        self.exe = self.cursor.execute
        self.exem = self.cursor.executemany
        self.fetchall = self.cursor.fetchall
        self.limit = 10000

    @staticmethod
    def check_list_not_empty(L) -> list or tuple:
        """
        Raise error if L == [] or ().
        Raise error if L is not list or tuple.
        Else, return L.

        :param L: List or tuple
        :return:
        """
        if not (isinstance(L, list) or isinstance(L, tuple)):
            raise TypeError('Not a list or tuple.')
        if L == []:
            raise ValueError('Empty list.')
        if L == ():
            raise ValueError('Empty tuple.')
        return L

    @staticmethod
    def utc_to_jst(dt):
        if not isinstance(dt, datetime):
            raise TypeError('Must be datetime.')
        return dt + timedelta(hours=+9)

    @staticmethod
    def jst_to_utc(dt):
        if not isinstance(dt, datetime):
            raise TypeError('Must be datetime.')
        return dt + timedelta(hours=-9)

    def pdq(self, query, params=None, index_col=None):
        df = psql.read_sql_query(query, self.cnx,
                                 params=params, index_col=index_col)
        return df

    def q_all(self, query, params):
        """
        Query and fetchall().
        Return [(value11, value12, ...), (value21, value22, ...) ...]
        Return [] if not found.

        :param query:
        :param params:
        :return:
        :rtype: list of tuple
        """
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def q_row(self, query, params) -> tuple:
        """
        Return (value11, value12, ...)
        Return () if not found.
        Raise error if not unique.

        :param query:
        :param params:
        :return:
        """
        resp = self.q_all(query, params)
        if resp == []:
            return ()
        if len(resp) == 1:
            return resp[0]
        if len(resp) > 1:
            raise RuntimeError('Many row found. resp: {}'.format(resp))
        raise RuntimeError('Error. resp: {}'.format(resp))

    def q_col(self, query, params) -> list:
        """
        Return [value11, value21, ...]
        Return [] if not found.
        Raise error if number of select field is not 1.

        :param query:
        :param params:
        :return:
        """
        resp = self.q_all(query, params)
        if resp == []:
            return []
        if len(resp[0]) == 1:
            return [x[0] for x in resp]
        if len(resp[0]) > 1:
            raise RuntimeError('Selected many values. resp: {}'.format(resp))
        raise RuntimeError('Error. resp: {}'.format(resp))

    def q_single(self, query, params) -> object:
        """
        Return int, str or so on.
        Return None if not found.
        Raise error if found many.

        :param query:
        :param params:
        :return:
        """
        resp = self.q_col(query, params)
        if resp == []:
            return None
        if len(resp) == 1:
            return resp[0]
        if len(resp) > 1:
            raise RuntimeError('Many row found. resp: {}'.format(resp))
        raise RuntimeError('Error. resp: {}'.format(resp))

    def q_all_abs(self, query, params):
        """
        Query and fetchall().
        Return [(value11, value12, ...), (value21, value22, ...) ...]
        Raise error if not found.

        :param query:
        :param params:
        :return:
        :rtype: list of tuple
        """
        try:
            return self.check_list_not_empty(self.q_all(query, params))
        except ValueError:
            raise RuntimeError('Not found.')

    def q_row_abs(self, query, params) -> tuple:
        """Same as q_row except raising error if not found.

        :param query:
        :param params:
        :return:
        """
        try:
            return self.check_list_not_empty(self.q_row(query, params))
        except ValueError:
            raise RuntimeError('Not found.')

    def q_col_abs(self, query, params) -> list:
        """
        Same as q_col, but raise error if not found.

        :param query:
        :param params:
        :return:
        """
        try:
            return self.check_list_not_empty(self.q_col(query, params))
        except ValueError:
            raise RuntimeError('Not found.')

    def q_single_abs(self, query, params) -> object:
        """
        Same as q_single, except raising error if not found.

        :param query:
        :param params:
        :return:
        """
        ret = self.q_single(query, params)
        if ret is None:
            raise RuntimeError('Not found.')
        return ret




class TestMySqlHandler(unittest2.TestCase):
    def setUp(self):
        self.my = MySqlHandler()

        # Create a table for test
        oper = ('CREATE TABLE master_db.test_table'
                '('
                '    id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,'
                '    dt DATETIME,'
                '    num INT'
                ');')
        self.my.cursor.execute(oper)
        oper = 'INSERT INTO test_table VALUES (%s, %s, %s)'
        self.dt1 = datetime.utcnow().replace(microsecond=0)
        self.dt2 = self.dt1 + timedelta(-1)
        self.val1 = 1
        self.val2 = 2
        self.data = [(1, self.dt1, self.val1), (2, self.dt2, self.val2)]
        self.my.cursor.executemany(oper, self.data)

        self.q_all= 'SELECT * FROM test_table'
        self.q_dt = 'SELECT dt FROM test_table'
        self.q_where_id = 'SELECT * FROM test_table WHERE id=%s'
        self.q_dt_where_id = 'SELECT dt FROM test_table WHERE id=%s'

    def tearDown(self):
        # Drop test table
        oper = 'DROP TABLE test_table'
        self.my.cursor.execute(oper)
        self.my.cnx.close()

    def test_check_list_not_empty(self):
        f = self.my.check_list_not_empty
        self.assertEqual(f([0]), [0])
        self.assertEqual(f([0, 1]), [0, 1])
        with self.assertRaises(ValueError):
            f([])
        with self.assertRaises(TypeError):
            f(0)

    def test_q_all(self):
        self.assertEqual(self.my.q_all(self.q_all, None),
                         [(1, self.dt1, self.val1), (2, self.dt2, self.val2)])
        self.assertEqual(self.my.q_all(self.q_dt, None),
                         [(self.dt1,), (self.dt2,)])
        self.assertEqual(self.my.q_all(self.q_where_id, (1,)),
                         [(1, self.dt1, self.val1)])
        self.assertEqual(self.my.q_all(self.q_where_id, (999,)), [])

    def test_q_row(self):
        with self.assertRaises(RuntimeError):
            self.my.q_row(self.q_all, None)
        with self.assertRaises(RuntimeError):
            self.my.q_row(self.q_dt, None)
        self.assertEqual(self.my.q_row(self.q_where_id, (1,)),
                         (1, self.dt1, self.val1))
        self.assertEqual(self.my.q_row(self.q_where_id, (999,)), ())

    def test_q_col(self):
        with self.assertRaises(RuntimeError):
            self.my.q_col(self.q_all, None)
        self.assertEqual(self.my.q_col(self.q_dt, None), [self.dt1, self.dt2])
        with self.assertRaises(RuntimeError):
            self.my.q_col(self.q_where_id, (1,))
        self.assertEqual(self.my.q_col(self.q_where_id, (999,)), [])

    def test_q_single(self):
        with self.assertRaises(RuntimeError):
            self.my.q_single(self.q_all, None)
        with self.assertRaises(RuntimeError):
            self.my.q_single(self.q_dt, None)
        with self.assertRaises(RuntimeError):
            self.my.q_single(self.q_where_id, (1,))
        self.assertEqual(self.my.q_single(self.q_where_id, (999,)), None)
        self.assertEqual(self.my.q_single(self.q_dt_where_id, (999,)), None)
        self.assertEqual(self.my.q_single(self.q_dt_where_id, (1,)), self.dt1)

    def test_q_all_abs(self):
        self.assertEqual(self.my.q_all(self.q_all, None),
                         [(1, self.dt1, self.val1), (2, self.dt2, self.val2)])
        self.assertEqual(self.my.q_all(self.q_dt, None),
                         [(self.dt1,), (self.dt2,)])
        self.assertEqual(self.my.q_all(self.q_where_id, (1,)),
                         [(1, self.dt1, self.val1)])
        with self.assertRaises(RuntimeError):
            self.my.q_all_abs(self.q_where_id, (999,))

    def test_q_row_abs(self):
        with self.assertRaises(RuntimeError):
            self.my.q_row_abs(self.q_all, None)
        with self.assertRaises(RuntimeError):
            self.my.q_row_abs(self.q_dt, None)
        self.assertEqual(self.my.q_row_abs(self.q_where_id, (1,)),
                         (1, self.dt1, self.val1))
        with self.assertRaises(RuntimeError):
            self.my.q_row_abs(self.q_where_id, (999,))

    def test_q_col_abs(self):
        with self.assertRaises(RuntimeError):
            self.my.q_col_abs(self.q_all, None)
        self.assertEqual(self.my.q_col_abs(self.q_dt, None),
                         [self.dt1, self.dt2])
        with self.assertRaises(RuntimeError):
            self.my.q_col_abs(self.q_where_id, (1,))
        with self.assertRaises(RuntimeError):
            self.my.q_col_abs(self.q_where_id, (999,))

    def test_q_single_abs(self):
        with self.assertRaises(RuntimeError):
            self.my.q_single_abs(self.q_all, None)
        with self.assertRaises(RuntimeError):
            self.my.q_single_abs(self.q_dt, None)
        with self.assertRaises(RuntimeError):
            self.my.q_single_abs(self.q_where_id, (1,))
        with self.assertRaises(RuntimeError):
            self.my.q_single_abs(self.q_where_id, (999,))
        with self.assertRaises(RuntimeError):
            self.my.q_single_abs(self.q_dt_where_id, (999,))
        self.assertEqual(self.my.q_single_abs(self.q_dt_where_id, (1,)),
                         self.dt1)

if __name__ == "__main__":
    unittest2.main()
