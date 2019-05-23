import numpy as np
import pandas as pd
from sqlalchemy import create_engine

# 连接数据库并写和读数据
engine = create_engine('mysql+pymysql://root:root@localhost:3306/test')
order = pd.read_csv('sample-orders.csv')
order.to_sql('rfm_analysis',con = engine,index = False,if_exists = 'replace')
print('Write to Mysql successfully!')
sql = '''SELECT * FROM rfm_analysis'''
orders = pd.read_sql_query(sql,engine)

# 时间转换并计算购买时间差
orders['order_date'] = pd.to_datetime(orders['order_date'])
orders['date_diff'] = pd.to_datetime('today') - orders['order_date']
orders['date_diff'] = orders['date_diff'].dt.days

# 计算R、F、M的值，得到RFM表
R_Agg = orders.groupby('customer').date_diff.agg({'date_diff':np.min})
F_Agg = orders.groupby('customer').order_id.agg({'order_id':np.size})
M_Agg = orders.groupby('customer').grand_total.agg({'grand_total':np.sum})
aggOrder = R_Agg.join(F_Agg).join(M_Agg)
aggOrder.rename(columns={'date_diff': 'recency',
                         'order_id': 'frequency',
                         'grand_total': 'monetary_value'}, inplace=True)

# R、F、M各项分值
bins = aggOrder.recency.quantile(q = [0,0.2,0.4,0.6,0.8,1],interpolation = 'nearest')
bins[0] = 0
labels = [5,4,3,2,1]
aggOrder['R_S'] = pd.cut(aggOrder.recency,bins = bins,labels = labels)

bins = aggOrder.frequency.quantile(q = [0,0.2,0.4,0.6,0.8,1],interpolation = 'nearest')
bins[0] = 0
labels = [5,4,3,2,1]
aggOrder['F_S'] = pd.cut(aggOrder.frequency,bins = bins,labels = labels)

bins = aggOrder.monetary_value.quantile(q = [0,0.2,0.4,0.6,0.8,1],interpolation = 'nearest')
bins[0] = 0
labels = [5,4,3,2,1]
aggOrder['M_S'] = pd.cut(aggOrder.monetary_value,bins = bins,labels = labels)

# 归总RFM值并分类，一共8个类
aggOrder['RFM'] = 100 * aggOrder['R_S'].astype(int) + 10 * aggOrder['F_S'].astype(int) + 1 * aggOrder['M_S'].astype(int)
bins = aggOrder.RFM.quantile(q = [0,0.125,0.25,0.375,0.5,0.625,0.75,0.875,1],interpolation = 'nearest')
bins[0] = 0
labels = ['潜在客户','一般发展客户','一般保持客户','一般价值客户',
          '重点挽留客户','重点发展客户','重点保持客户','高价值客户']
aggOrder['level'] = pd.cut(aggOrder.RFM,bins = bins,labels = labels)
aggOrder = aggOrder.reset_index()

# 将分类结果存入Mysql
rmfClass = aggOrder.groupby('level').customer.agg({'size':np.size}).reset_index()
rmfClass.to_sql('rfm_class',con = engine,index = False,if_exists = 'replace')
print('Write to Mysql successfully!')
print(rmfClass)