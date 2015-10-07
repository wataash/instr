# Std libs
import json
import os.path
import sqlite3
# Non-std libs
import matplotlib.pyplot as plt


with open(os.path.expanduser('~') + '/Dropbox/master-db/src-master-db/pa300_config.json') as f:
    j = json.load(f)
sample = j['sample']
mesas = j['plt_mesas']

conn_params = sqlite3.connect(j['db_params_file'].replace('home', os.path.expanduser('~')))
cur_params = conn_params.cursor()

#sample, X_min, X_max, Y_min, Y_max = \
#    cur_params.execute('SELECT sample, min_X, max_X, min_Y, max_Y \
#                        FROM samples WHERE id=?',
#                        (sample,)).fetchone()
#mesa, area = \
#    cur_params.execute('SELECT name, area \
#                        FROM mesas WHERE id=?',
#                        (str(j['mesa_id']),)).fetchone()

Xs = {}
Rs = {}
for mesa in mesas:
    XYRs = cur_params.execute('SELECT X,Y,R FROM resistance WHERE sample=? AND mesa=? AND Y>=9', (sample, mesa)).fetchall()
    Xs[mesa] = [XYR[0] for XYR in XYRs]
    Rs[mesa] = [XYR[2] for XYR in XYRs]
    plt.semilogy(Xs[mesa],Rs[mesa], 'o', label=mesa)
    plt.legend(loc=2)
    #plt.ylim([1e3, 1e8])
plt.show()

conn_params.close()
conn_IVs.close()
