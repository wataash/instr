# Std libs
import os
import sqlite3

data_dir = os.path.expanduser('~') + '/Documents/Agilent4156C'
dict_param = {}

sqlite3_file_name = os.path.expanduser('~') + '/Documents/instr_data/IV.sqlite3'
sqlite3_connection = sqlite3.connect(sqlite3_file_name)
cursor = sqlite3_connection.cursor()


with open(data_dir + '/double-sweep_params.csv') as f:
    tmp = f.readlines()
    for L in tmp:
        # t0=20150725-173549,sample=sample,X=6,Y=1,xpos=6909.588283754738,ypos=412.4674990964116,mesa=mesa,status=255,measPoints=2002,comp=0.01,instr=SUSS PA200, originalFileName=double-sweep_20150725-173549_E0326-2-1_X6_Y1_mesa_-0.1V.csv
        t0 = int(L.split(',')[0][3:].replace('-', ''))  # 20150725-173549
        dict_param[t0] = L

cnt = 0
for fname in os.listdir(data_dir):
    # double-sweep_20150725-171113_sample_X6_Y1_mesa_-0.1V.csv
    if not fname.startswith('double-sweep_2015'):
        print('skip', fname)
        continue
    with open(data_dir + '/' + fname) as f:
        t0 = int(f.name.split('_')[1].replace('-', ''))
        Vs, Is = f.read().split()
    
    Vs = [float(V) for V in Vs.split(',')]
    Is = [float(I) for I in Is.split(',')]
    
    cnt += 1
    param = dict_param[t0].split(',')
    print(cnt, param)

    sample = param[1][7:]
    X = int(param[2][2:])
    Y = int(param[3][2:])
    xpos = float(param[4][5:])
    ypos = float(param[5][5:])
    mesa = param[6][5:]
    status = int(param[7][7:])
    points = int(param[8][11:])
    comp = float(param[9][5:])
    instr = param[10][6:]
    if min(Vs) == 0:
        volt = max(Vs)
    else:
        volt = min(Vs)

    cursor.execute('INSERT INTO parameters VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                   (t0, sample, X, Y, xpos, ypos, mesa, status, points, comp, volt, instr))
    tmp = zip([t0] * points, Vs, Is)  # [(t0, V0, I0), (t0, V1, I1), ...]
    cursor.executemany('''INSERT INTO IV(t0, V, I) VALUES(?, ?, ?)''', tmp)  # IV.id: autofilled
    sqlite3_connection.commit()

print(0)
