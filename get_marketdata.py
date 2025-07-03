import tushare as ts
import pandas as pd
from datetime import datetime

pro = ts.pro_api('请输入token')
start_date='20180101'#起始日期可自定义,没必要用太早的数据
today = datetime.today().strftime('%Y%m%d')

df = pro.daily(ts_code='000001.SZ', start_date=start_date, end_date=today)
df.to_csv('marketdata.csv',index=False)