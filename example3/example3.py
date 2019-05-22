# 导入模块
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('ggplot')

# 加载数据
columns = ['user_id','order_dt','order_products','order_amount']
df = pd.read_csv('CDNOW_master.txt',names = columns,sep = '\s+') # '\s+'表示匹配任意空白符
df['order_date'] = pd.to_datetime(df.order_dt,format = "%Y%m%d") # to_datetime可以将特定的字符串或者数字转换成时间格式
df['month'] = df.order_date.values.astype('datetime64[M]')

# 多维度统计数据，发现趋势异常
user_grouped = df.groupby('user_id').sum()
plt.figure(1)
df.groupby('month').order_products.sum().plot()
plt.title('order_products')
plt.figure(2)
df.groupby('month').order_amount.sum().plot()
plt.title('order_amount')
# 从销量和金额分析
df.plot.scatter(x = 'order_amount', y = 'order_products')
df.groupby('user_id').sum().plot.scatter(x = 'order_amount',y = 'order_products')
plt.figure(figsize = (12,4))
plt.subplot(121)
df.groupby('user_id').order_amount.sum().hist(bins = 30) # 为何不进行用户分组，且分组后运行超慢
plt.subplot(122)
df.groupby('user_id').order_products.sum().hist(bins = 30)
plt.show()
# 从消费时间节点分析
print(df.groupby('user_id').month.min().value_counts()) # value_counts和count区别
print(df.groupby('user_id').month.max().value_counts())

# 复购率
pivoted_counts = df.pivot_table(index = 'user_id',columns = 'month',
                                values = 'order_dt',aggfunc = 'count').fillna(0)
columns_month = df.month.sort_values().astype('str').unique() # 去重
pivoted_counts.columns = columns_month
pivoted_counts_transf = pivoted_counts.applymap(lambda x: 1 if x > 1 else np.NaN if x == 0 else 0) # applymap针对DataFrame里的所有数据
(pivoted_counts_transf.sum()/pivoted_counts_transf.count()).plot(figsize = (10,4))

# 回购率
pivoted_amount = df.pivot_table(index = 'user_id',columns = 'month',
                                values = 'order_amount',aggfunc = 'mean').fillna(0)
columns_month = df.month.sort_values().astype('str').unique()
pivoted_amount.columns = columns_month
pivoted_purchase = pivoted_amount.applymap(lambda x: 1 if x > 0 else 0)

def purchase_return(data):
    status = []
    for i in range(17):
        if data[i] == 1:
            if data[i+1] == 1:
                status.append(1)
            if data[i+1] == 0:
                status.append(0)
        else:
            status.append(np.NaN)
    status.append(np.NaN)
    return status

pivoted_purchase_return = pivoted_purchase.apply(purchase_return,axis = 1)
pivoted_purchase_return = pivoted_purchase.apply(lambda x: pd.Series(purchase_return(x)),axis = 1)
(pivoted_purchase_return.sum()/pivoted_purchase_return.count()).plot(figsize = (10,4))

# 新客户：第一次消费
# 活跃用户：某一个时间窗口内有过消费的老客
# 不活跃用户：时间窗内没有消费过的老客
# 回流用户：上一个窗口没有消费，而当前时间窗口有过消费

def active_status(data):
    status = []
    for i in range(18):
        # 若本月没有消费，一种可能是新客户都不算，一种可能是不活跃的老客户
        if data[i] == 0:
            if len(status) > 0:
                if status[i-1] == 'unreg':
                    status.append('unreg')
                else:
                    status.append('unactive')
            else:
                status.append('unreg')
        # 若本月有消费
        else:
            if len(status) == 0:
                status.append('new')
            else:
                if status[i-1] == 'unactive':
                    status.append('return')
                elif status[i-1] == 'unreg':
                    status.append('new')
                else:
                    status.append('active')
    return status
pivoted_purchase_status = pivoted_purchase.apply(lambda x: pd.Series(active_status(x)),axis = 1)
purchase_status_counts = pivoted_purchase_status.replace('unreg',np.NaN).apply(lambda x: pd.value_counts(x))
purchase_status_counts.fillna(0).T.plot.area(figsize = (12,6))

return_rata = purchase_status_counts.apply(lambda x:x/x.sum(),axis = 1)
return_rata.loc['return'].plot(figsize = (12,6))
return_rata.loc['active'].plot(figsize = (12,6))
plt.show()

# 用户质量分析
# 金额
user_amount = df.groupby('user_id').order_amount.sum().sort_values().reset_index()
user_amount['amount_cumsum'] = user_amount.order_amount.cumsum() # 逐行计算累计的金额，最后的2500315便是总消费额。
amount_total = user_amount.amount_cumsum.max()
user_amount['prop'] = user_amount.apply(lambda x:x.amount_cumsum / amount_total,axis =1)
user_amount.prop.plot()
# 销量
user_counts = df.groupby('user_id').order_dt.count().sort_values().reset_index()
user_counts['counts_cumsum'] = user_counts.order_dt.cumsum()
counts_total = user_counts.counts_cumsum.max()
user_counts['prop'] = user_counts.apply(lambda x:x.counts_cumsum / counts_total,axis =1)
user_counts.prop.plot()

# # 计算用户生命周期
user_purchase = df[['user_id','order_products','order_amount','order_date']]
order_date_min = user_purchase.groupby('user_id').order_date.min()
order_date_max = user_purchase.groupby('user_id').order_date.max()
((order_date_max - order_date_min)/np.timedelta64(1,'D')).hist(bins = 15)
life_time = (order_date_max - order_date_min).reset_index()
life_time['life_time'] = life_time.order_date / np.timedelta64(1,'D')
life_time[life_time.life_time > 0].life_time.hist(bins = 100,figsize = (12,6))

# 留存率
user_purchase_retention = pd.merge(left = user_purchase,right = order_date_min.reset_index(),
                                   how = 'inner', on = 'user_id',
                                   suffixes = ('','_min'))
user_purchase_retention['order_date_diff'] = user_purchase_retention.order_date - user_purchase_retention.order_date_min
date_trans = lambda x:x/np.timedelta64(1,'D')
user_purchase_retention['date_diff'] = user_purchase_retention.order_date_diff.apply(date_trans)
bin = [0,3,7,15,30,60,90,180,365]
user_purchase_retention['date_diff_bin'] = pd.cut(user_purchase_retention.date_diff, bins = bin)
pivoted_retention = user_purchase_retention.pivot_table(index = ["user_id"],columns = ["date_diff_bin"],
                                                        values = ["order_amount"],aggfunc = [np.sum])

pivoted_retention.mean()
pivoted_retention_trans = pivoted_retention.fillna(0).applymap(lambda x:1 if x > 0 else 0)
(pivoted_retention_trans.sum() / pivoted_retention_trans.count()).plot.bar()

# 平均购买周期
grouped = user_purchase_retention.groupby('user_id')
def diff(group):
    d = group.date_diff - group.date_diff.shift(-1)
    return d
last_diff = user_purchase_retention.groupby('user_id').apply(diff)
last_diff.hist(bins = 20)
plt.show()