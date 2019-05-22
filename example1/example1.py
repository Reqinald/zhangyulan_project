import pandas as pd
import numpy as np
from pandas import DataFrame,Series
import pymysql


def connection(database_key):
    mysql = {'host':'127.0.0.1','port':3306,'user':'root','passwd':'root','db':'','charset':'utf8'}
    if database_key == 'test':
        mysql['db'] = 'test'
    elif database_key == 'abc':
        mysql['db'] = 'abc'
    elif database_key == 'experiment':
        mysql['db'] = 'experiment'
    else:
        mysql['db'] = 'example'
    return mysql

# 创建连接
db = 'example'
conn = pymysql.connect(**connection(db))

# 创建游标
cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
# cursor = conn.cursor()

cursor.execute('DELETE FROM example1 WHERE isDA=0')
def read_table(cur,sql_order):
    cur.execute(sql_order)
    data = cur.fetchall()
    frame = pd.DataFrame(list(data))
    return frame

data = read_table(cursor,'SELECT * FROM example1')
print(data)
conn.commit()
cursor.close()
conn.close()

# print(pd.crosstab(data.city,data.companySize))