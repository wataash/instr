import os
import sqlite3

data_dir = os.path.expanduser('~') + r'\Documents\Agilent4156C\double-sweep'

for fname in [fname_all for fname_all in os.listdir(data_dir) if
              fname_all.startswith('double-sweep') and
              'D169' in fname_all and
              'E0326-2-1' in fname_all]:
    with open(data_dir + '\\' + fname) as f:
        tmp = f.name.split('_')
        datetime = tmp[1]  # '20150725-171113'
        # read = f.read().split()
        raise NotImplementedError

print(0)
