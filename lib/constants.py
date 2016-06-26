import os

import keyring


# Commons
# home = os.path.expanduser('~/')

mysql_config = {
    'user': 'wsh',
    'password': keyring.get_password('rds', 'wsh'),
    'database': 'master_db',
    'host': 'mysql1.foobar.ap-northeast-1.rds.amazonaws.com',
    'port': '3306'
    }
if mysql_config['password'] is None:
    raise RuntimeError('Set password before: '
                       'import keyring; '
                       "keyring.set_password('rds', 'wsh', 'password')")
