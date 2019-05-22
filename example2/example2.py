# 导入模块
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from wordcloud import WordCloud

# 连接数据库，MySQL用户：root，密码：root，端口：3306，数据库：example
engine = create_engine('mysql+pymysql://root:root@localhost:3306/example')
# 读取数据，df类型为DataFrame
sql = '''SELECT * FROM example2'''
df = pd.read_sql_query(sql,engine)

# 查看positionId重复数据，共有5031条不重复数据
len(df.positionId.unique())
# 删除positionId重复项，subset:去重基准列，keep:'first'保留第一个，删除余后重复，'last'删除前面，保留最后
df_duplicates = df.drop_duplicates(subset = 'positionId',keep = 'first')
# salary分列，计算最低和最高工资，upper:全部大写
def cut_word(word,method):
    position = word.find('-')
    length = len(word)
    if position != -1:
        bottomSalary = word[:position-1]
        topSalary = word[position + 1:length - 1]
    else:
        bottomSalary = word[:word.upper().find('K')]
        topSalary = bottomSalary
    if method == 'bottom':
        return bottomSalary
    else:
        return topSalary
# apply中，参数是添加在函数后面，而不是里面,axis=1表示行，axis=0表示列
df_duplicates['bottomSalary'] = df_duplicates.salary.apply(cut_word,method = 'bottom')
df_duplicates['topSalary'] = df_duplicates.salary.apply(cut_word,method = 'top')
df_duplicates.bottomSalary=df_duplicates.bottomSalary.astype('int')
df_duplicates.topSalary=df_duplicates.topSalary.astype('int')
df_duplicates['avgSalary'] = df_duplicates.apply(lambda x:(x.bottomSalary + x.topSalary)/2, axis = 1)
# print(df_duplicates[['city','salary','bottomSalary','topSalary','avgSalary']])

# 切选部分数据
df_clean = df_duplicates[['city','companyShortName','companySize','education','positionName','positionLables',
                          'workYear','avgSalary']]
# 对数据进行统计，value_counts计数，统计所有非零元素的个数，并以降序方式输出Series
# print(df_clean.city.value_counts())
# print(df_clean.describe())

# 绘图
plt.style.use('ggplot')
# df_clean.avgSalary.hist(bins = 15)
# 获取中文字体位置
font_zh = FontProperties(fname = "C:\Windows\Fonts\SimSun.ttc")
# 箱线图，by是选择分类变
ax_box_1 = df_clean.boxplot(column = 'avgSalary',by = 'workYear',figsize = (9,7))
for label in ax_box_1.get_xticklabels():
    label.set_fontproperties(font_zh)
ax_box_2 = df_clean.boxplot(column = 'avgSalary',by = 'city',figsize = (9,7))
for label in ax_box_2.get_xticklabels():
    label.set_fontproperties(font_zh)
df_sh_bj = df_clean[df_clean['city'].isin(['上海','北京'])]
ax_box_3 = df_sh_bj.boxplot(column = 'avgSalary',by = ['city','education'],figsize = (9,7))
for label in ax_box_3.get_xticklabels():
    label.set_fontproperties(font_zh)
# # 多维度分析
# print(df_clean.groupby('city').count()) # 按城市分组，对每个字段进行统计个数
# print(df_clean.groupby('city').mean()) # 只针对数值，因此只有avgSalary
# unstack方法，进行行列转置
# print(df_clean.groupby(['city','education']).mean().unstack()) # 统计不同城市不同学历的平均工资
# print(df_clean.groupby(['city','education']).avgSalary.count().unstack()) # 统计不同城市不同学历的招聘人数
# print(df_clean.groupby('companyShortName').avgSalary.agg(['count','mean']).sort_values(by = 'count',ascending=False)) # 不同公司的招聘人数和平均工资统计
# print(df_clean.groupby('companyShortName').avgSalary.agg(lambda x:max(x)-min(x))) # 不同公司最高薪资和最低薪资差值
# # 前5
# def topN(df,n=5):
#     counts = df.value_counts()
#     return counts.sort_values(ascending = False)[:n]
# print(df_clean.groupby('city').companyShortName.apply(topN))
# print(df_clean.groupby('city').positionName.apply(topN))
# 不同维度绘图
ax_bar_1 = df_clean.groupby('city').mean().plot.bar()
for label in ax_bar_1.get_xticklabels():
    label.set_fontproperties(font_zh)
ax_bar_2 = df_clean.groupby(['city','education']).mean().unstack().plot.bar(figsize=(14,6))
for label in ax_bar_2.get_xticklabels():
    label.set_fontproperties(font_zh)
ax_bar_2.legend(prop = font_zh)

# plt.hist(x = df_clean[df_clean.city == '上海'].avgSalary,
#          bins = 15,
#          normed = -1,
#          facecolor = 'blue',
#          alpha = 0.5)
# plt.hist(x = df_clean[df_clean.city == '背景'].avgSalary,
#          bins = 15,
#          normed = -1,
#          facecolor = 'red',
#          alpha = 0.5)
# 数据分段
bins = [0,3,5,10,15,20,30,100] # 分段数值
level = ['0~3','3~5','5~10','10~15','15~20','20~30','30+'] # 分段标签
df_clean['level'] = pd.cut(df_clean['avgSalary'],bins = bins,labels = level)
# print(df_clean[['avgSalary','level']])
df_level = df_clean.groupby(['city','level']).avgSalary.count().unstack()
df_level_prop = df_level.apply(lambda x:x/x.sum(),axis = 1) # 不同段工资所占的百分比
ax_bar_3 = df_level_prop.plot.bar(stacked = True,figsize = (14,6))
for label in ax_bar_3.get_xticklabels():
    label.set_fontproperties(font_zh)

word = df_clean.positionLables.str[1:-1].replace(' ','') # 去掉两遍'[]'，以及用','替换空格
df_word = word.dropna().str.split(',').apply(pd.value_counts)
df_word_counts = df_word.unstack().dropna().reset_index().groupby('level_0').count()
# print(df_word_counts.index)

df_word_counts.index = df_word_counts.index.str.replace("'","")
wordcloud = WordCloud(font_path = "C:\Windows\Fonts\SimSun.ttc",
                      width = 900,height = 400,
                      background_color = 'white')
f,axs = plt.subplots(figsize = (15,15))
wordcloud.fit_words(df_word_counts.level_1)
ax = plt.imshow(wordcloud)
plt.axis('off')
plt.show()
