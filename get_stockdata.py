import tushare as ts
import pandas as pd
import time
import os
from datetime import datetime
from collections import Counter


# 初始化接口
pro = ts.pro_api('请输入token')
start_date = '20220101'  # 起始日期可自定义,没必要用太早的数据
today = datetime.today().strftime('%Y%m%d')
stock_list = pd.read_excel("自动化设备.xlsx")

# 创建存储数据的目录
if not os.path.exists('pricedata'):
    os.makedirs('pricedata')
if not os.path.exists('dailydata'):
    os.makedirs('dailydata')

# 用于存储每只股票的数据长度
price_lengths = {}
basic_lengths = {}

# 获得股票历史价格还可以计算动量因子
for stockcode in stock_list['ts_code']:
    try:
        temp_data = pro.daily(ts_code=stockcode, start_date=start_date, end_date=today)
        if not temp_data.empty:
            # 记录数据长度
            price_lengths[stockcode] = len(temp_data)
            temp_data.to_csv(f'pricedata/{stockcode[:6]}.csv', index=False)
            time.sleep(0.1)
            print(f'{stockcode} 价格数据下载完成，长度: {len(temp_data)}')
    except Exception as e:
        print(f'下载{stockcode}价格数据时出错: {e}')

# 两个经典价值因子 P/E P/B
for stockcode in stock_list['ts_code']:
    try:
        daily_data = pro.daily_basic(ts_code=stockcode, start_date=start_date, end_date=today, fields='ts_code,trade_date,pe,pb')
        if not daily_data.empty:
            # 记录数据长度
            basic_lengths[stockcode] = len(daily_data)
            daily_data.to_csv(f'dailydata/{stockcode[:6]}.csv', index=False)
            time.sleep(0.1)
            print(f'{stockcode} 基本面数据下载完成，长度: {len(daily_data)}')
        else:
            print(f'{stockcode} 基本面数据为空')
    except Exception as e:
        print(f'下载{stockcode}基本面数据时出错: {e}')

# 分析价格数据长度，找出最常见的数据长度
if price_lengths:
    price_counter = Counter(price_lengths.values())
    most_common_price_length = price_counter.most_common(1)[0][0]
    
    # 保留最常见长度的股票数据，删除其他的
    for stockcode, length in price_lengths.items():
        if length != most_common_price_length:
            try:
                import os
                os.remove(f'pricedata/{stockcode[:6]}.csv')
                print(f'删除价格数据不完整的股票: {stockcode}')
            except Exception as e:
                print(f'删除{stockcode}价格数据文件时出错: {e}')

# 分析基本面数据长度，找出最常见的数据长度
if basic_lengths:
    basic_counter = Counter(basic_lengths.values())
    most_common_basic_length = basic_counter.most_common(1)[0][0]
    
    # 保留最常见长度的股票数据，删除其他的
    for stockcode, length in basic_lengths.items():
        if length != most_common_basic_length:
            try:
                import os
                os.remove(f'dailydata/{stockcode[:6]}.csv')
                print(f'删除基本面数据不完整的股票: {stockcode}')
            except Exception as e:
                print(f'删除{stockcode}基本面数据文件时出错: {e}')