import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sqlalchemy import create_engine
from sklearn.manifold import TSNE
from datetime import datetime

# inputdate = '2013-01-01'
# NOW = datetime.strptime(inputdate, "%Y-%m-%d")
outputfile = 'E:/dataAnalysis/julei.csv'
engine = create_engine('mysql+pymysql://root:root@localhost:3306/test')
order = pd.read_csv('sample-orders.csv')
order.to_sql('k_means',con = engine,index = False,if_exists = 'replace')
print('Write to Mysql successfully!')
sql = '''SELECT * FROM k_means'''
orders = pd.read_sql_query(sql,engine)
orders['order_date'] = pd.to_datetime(orders['order_date'])

# 探索性分析
explore = orders.describe(percentiles=[],include = 'all').T
explore['null'] = len(orders) - explore['count'] # 计算空值数
explore = explore[['null','max','min']]
explore.columns = [u'空值数',u'最大值',u'最小值']
# print('-------------------------探索性分析数据')
# print(explore)

# 数据预处理
orders['date_diff'] = pd.to_datetime('today') - orders['order_date']
# orders['date_diff'] = NOW - orders['order_date']
orders['date_diff'] = orders['date_diff'].dt.days
R_Agg = orders.groupby('customer').agg({'date_diff':np.min})
F_Agg = orders.groupby('customer').order_id.agg({'order_id':np.size})
M_Agg = orders.groupby('customer').grand_total.agg({'grand_total':np.sum})
aggOrder_y = R_Agg.join(F_Agg).join(M_Agg)
aggOrder_y.rename(columns={'date_diff': 'R',
                         'order_id': 'F',
                         'grand_total': 'M'}, inplace=True)
# print('-------------------------处理后数据')
# print(aggOrder_y)

# 数据变换
aggOrder = (aggOrder_y - aggOrder_y.mean()) / (aggOrder_y.std()) # 标准化
aggOrder.columns = ['Z' + i for i in aggOrder_y.columns]
# print('-------------------------数据变换')
# print(aggOrder)

# 模型构建
k = 5
kmodel = KMeans(n_clusters = k,n_jobs = 4,max_iter=500)
kmodel.fit(aggOrder)
r1 = pd.Series(kmodel.labels_).value_counts() # 统计各个类别的数目
r2 = pd.DataFrame(kmodel.cluster_centers_) # 找出聚类中心
r = pd.concat([r2,r1],axis = 1) # 横向连接(0是纵向)，得到聚类中心对应的类别下的数目
r.columns = list(aggOrder.columns) + [u'类别数目'] # 重命名表头
r = pd.concat([aggOrder_y,aggOrder,pd.Series(kmodel.labels_, index = aggOrder.index)], axis = 1)
r.columns = list(aggOrder_y.columns) + list(aggOrder.columns) + [u'level']
r.to_sql('rfm_class_julei',con = engine,index = False,if_exists = 'replace')
print('Write to Mysql successfully!')
r.to_csv(outputfile,sep=',',encoding='utf_8_sig')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
# for i in range(k):
#     cls = aggOrder[r[u'level']==i]
#     cls.plot(kind = 'kde',linewidth=2,subplots=True,sharex=False)
#     plt.suptitle('聚类类别=%d;样本数%d' % (i,r1[i]))
#     plt.legend()
#     plt.show()

clu = kmodel.cluster_centers_
x = [1,2,3]
colors = ['r','g','y','b','k','c','g','b']
for i in range(k):
    plt.plot(x,clu[i],label='clustre'+str(i),linewidth=9-i,color=colors[i],marker='o')
    # plt.plot(x,clu[i],label='clustre'+str(i),linewidth=9-i,color=colors[i])
plt.xlabel('R F M')
plt.ylabel('values')
plt.show()

# ts = TSNE()
# ts.fit_transform(r)
# ts = pd.DataFrame(ts.embedding_, index=r.index)
#
# a = ts[r[u'level'] == 0]
# plt.plot(a[0],a[1],'r.')
# a = ts[r[u'level'] == 1]
# plt.plot(a[0],a[1],'go')
# a = ts[r[u'level'] == 2]
# plt.plot(a[0],a[1],'b*')
# a = ts[r[u'level'] == 3]
# plt.plot(a[0],a[1],'k--')
# a = ts[r[u'level'] == 4]
# plt.plot(a[0],a[1],'mo')
# a = ts[r[u'level'] == 5]
# plt.plot(a[0],a[1],'r*')
# plt.show()