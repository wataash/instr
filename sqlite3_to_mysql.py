# Std libs
from datetime import datetime, timedelta
import sqlite3
# Non-std libs
import mysql.connector
import pymysql
# My libs
import constants as c

# http://dev.mysql.com/doc/connector-python/en/

cnx = mysql.connector.connect(**c.mysql_config)
cursor = cnx.cursor()


cursor.execute('INSERT INTO XY (X, Y) VALUES (1, 1)')

#add_VI_param1 = ('INSERT INTO VI_param '
#                 '(device_id, dt, points, comp, V, inst) '
#                 'VALUES (%s, %s, %s, %s, %s, %s)')
#data_VI_param1 = (1, datetime(2015, 11, 11), 101, 0.001, 0.010, 'test inst')
#cursor.execute(add_VI_param1, data_VI_param1)
#tmp = cursor.lastrowid

#one_hour_ago = datetime.now() + timedelta(hours=-1)
#add_VI_param2 = ('INSERT INTO VI_param '
#                 '(device_id, points, comp, V, inst) '
#                 'VALUES (%(dev_id)s, %(dt), %(p), %(c)s, %(V)s, %(i)s)')
#data_VI_param2 = {
#    'dev_id': 2,
#    'dt': one_hour_ago,
#    'p': 201,
#    'c': 0.001,
#    'V': 0.020,
#    'i': 'test inst 2'
#    }
#cursor.execute(add_VI_param2, data_VI_param2)
#tmp = cursor.lastrowid


cnx.commit()

cursor.close()
cnx.close()
