import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
import seaborn as sns
from matplotlib.ticker import PercentFormatter
from datetime import datetime

portfolio_num=10
start_date = '20220101'  # 起始日期与get_stockdata的预设一致
today = datetime.today().strftime('%Y%m%d')
stock_list = pd.read_excel("自动化设备.xlsx")
# 计算训练集和测试集的分割点（这里以70%作为训练集，30%作为测试集）
date_range = pd.date_range(start=start_date, end=today)
split_index = int(len(date_range) * 0.7)
split_date = date_range[split_index].strftime('%Y%m%d')


# 创建结果DataFrame
results = pd.DataFrame(columns=['ts_code'])

# 计算每支股票的回报率并排序
return_data = []
for stockcode in stock_list['ts_code']:
    try:
        # 读取价格数据
        price_file = f'pricedata/{stockcode[:6]}.csv'
        if os.path.exists(price_file):
            price_data = pd.read_csv(price_file)
            # 确保trade_date为字符串类型
            price_data['trade_date'] = price_data['trade_date'].astype(str)
            # 筛选测试集数据
            test_data = price_data[price_data['trade_date'] >= split_date]
            if not test_data.empty:
                # 计算平均日回报率
                test_data['daily_return'] = test_data['close'].pct_change()
                avg_return = test_data['daily_return'].mean()
                return_data.append({'ts_code': stockcode, 'avg_return': avg_return})
    except Exception as e:
        print(f"没有{stockcode}数据{e}")

# 按回报率从高到低排序
if return_data:
    return_df = pd.DataFrame(return_data)
    return_df['return_rank'] = return_df['avg_return'].rank(ascending=False)
    results = pd.merge(results, return_df[['ts_code', 'return_rank']], on='ts_code', how='outer')

# 计算每支股票的PE和PB并排序
pe_data = []
pb_data = []
for stockcode in stock_list['ts_code']:
    try:
        # 读取每日基本数据
        daily_file = f'dailydata/{stockcode[:6]}.csv'
        if os.path.exists(daily_file):
            daily_data = pd.read_csv(daily_file)
            # 确保trade_date为字符串类型
            daily_data['trade_date'] = daily_data['trade_date'].astype(str)
            # 筛选测试集数据
            test_data = daily_data[daily_data['trade_date'] >= split_date]
            if not test_data.empty:
                # 计算平均PE和PB
                avg_pe = test_data['pe'].mean()
                avg_pb = test_data['pb'].mean()
                pe_data.append({'ts_code': stockcode, 'avg_pe': avg_pe})
                pb_data.append({'ts_code': stockcode, 'avg_pb': avg_pb})
    except Exception as e:
        print(f"处理{stockcode}PE/PB时出错: {e}")

# 按PE从低到高排序
if pe_data:
    pe_df = pd.DataFrame(pe_data)
    pe_df['pe_rank'] = pe_df['avg_pe'].rank(ascending=True)
    results = pd.merge(results, pe_df[['ts_code', 'pe_rank']], on='ts_code', how='outer')

# 按PB从低到高排序
if pb_data:
    pb_df = pd.DataFrame(pb_data)
    pb_df['pb_rank'] = pb_df['avg_pb'].rank(ascending=True)
    results = pd.merge(results, pb_df[['ts_code', 'pb_rank']], on='ts_code', how='outer')

results=results.dropna()
# 计算综合排名
if not results.empty:
    # 计算平均排名
    results['average_rank'] = results[['return_rank', 'pe_rank', 'pb_rank']].mean(axis=1)
    # 选择排名最高的股票
    selected_stocks = results.nsmallest(portfolio_num, 'average_rank')
    print(f"\n综合排名最高的{portfolio_num}支股票:")
    print(selected_stocks)
    
    # 保存结果
    results.to_csv('factor_ranking_results.csv', index=False)
    selected_stocks.to_csv('selected_stocks.csv', index=False)
    print("因子排序完成，结果已保存至factor_ranking_results.csv")
    print("选股结果已保存至selected_stocks.csv")

# 回测部分
print("\n开始回测...")
# 读取选股结果
selected_stocks = pd.read_csv('selected_stocks.csv')
start_test_date = split_date  # 从之前的代码中获取测试期开始日期
end_test_date = today  # 测试期结束日期为当前日期

# 存储每只股票的每日价格数据
all_stock_prices = {}

# 读取每只股票的测试期价格数据
for stock_code in selected_stocks['ts_code']:
    try:
        stock_id = stock_code[:6]
        price_file = f'pricedata/{stock_id}.csv'
        
        if os.path.exists(price_file):
            price_data = pd.read_csv(price_file)
            price_data['trade_date'] = pd.to_datetime(price_data['trade_date'],format='%Y%m%d')  # 转换为datetime
            
            # 筛选测试期数据
            test_period_data = price_data[
                (price_data['trade_date'] >= pd.to_datetime(start_test_date,format='%Y%m%d')) & 
                (price_data['trade_date'] <= pd.to_datetime(end_test_date,format='%Y%m%d'))
            ]
            
            if not test_period_data.empty:
                # 按日期排序
                test_period_data = test_period_data.sort_values('trade_date')
                all_stock_prices[stock_code] = test_period_data[['trade_date', 'close']]
                print(f"成功加载 {stock_code} 的测试期价格数据")
            else:
                print(f"{stock_code} 在测试期内无价格数据")
        else:
            print(f"未找到 {stock_code} 的价格数据文件")
    except Exception as e:
        print(f"加载 {stock_code} 价格数据时出错: {e}")

# 读取大盘数据
try:
    market_data = pd.read_csv('marketdata.csv')
    market_data['trade_date'] = pd.to_datetime(market_data['trade_date'],format='%Y%m%d')  # 转换为datetime
    
    # 筛选测试期数据并按日期排序
    market_test_data = market_data[
        (market_data['trade_date'] >= pd.to_datetime(start_test_date,format='%Y%m%d')) & 
        (market_data['trade_date'] <= pd.to_datetime(end_test_date,format='%Y%m%d'))
    ].sort_values('trade_date')
    print("成功加载大盘测试期数据")
except Exception as e:
    print(f"加载大盘数据时出错: {e}")
    market_test_data = None
#————————————————————————————————————————

all_returns = pd.DataFrame()
for stock_code, df in all_stock_prices.items():
    df.sort_values('trade_date', inplace=True)
    df['Daily_Return'] = df['close'].pct_change()
    all_returns[stock_code] = df.set_index('trade_date')['Daily_Return']
all_returns['Avg_Return'] = all_returns.mean(axis=1)

result_df = pd.DataFrame({
    'trade_date': all_returns.index,
    'Avg_Daily_Return': all_returns['Avg_Return']
}).reset_index(drop=True)

result_df=result_df.set_index('trade_date')
market_test_data=market_test_data.set_index('trade_date')
result_df=pd.concat([result_df,market_test_data['pct_chg']/100],axis=1)
     


# 设置绘图样式
plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei", "STSong", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题
sns.set_style("whitegrid")
sns.set_palette('tab10')
sns.set(
    font=["SimHei", "Microsoft YaHei"],
    rc={"axes.unicode_minus": False}
)
def portfolio_analysis(result_df, portfolio_name='投资组合', market_name='大盘', 
                       risk_free_rate=0.03, trading_days=252):

    # 创建副本防止修改原始数据
    df = result_df.copy()
    
    # 1. 计算累计收益率
    df['Portfolio_Cumulative'] = (1 + df.iloc[:, 0]).cumprod()
    df['Market_Cumulative'] = (1 + df.iloc[:, 1]).cumprod()
    
    # 2. 计算最大回撤
    df['Portfolio_Peak'] = df['Portfolio_Cumulative'].cummax()
    df['Portfolio_Drawdown'] = (df['Portfolio_Cumulative'] - df['Portfolio_Peak']) / df['Portfolio_Peak']
    
    df['Market_Peak'] = df['Market_Cumulative'].cummax()
    df['Market_Drawdown'] = (df['Market_Cumulative'] - df['Market_Peak']) / df['Market_Peak']
    
    portfolio_mdd = df['Portfolio_Drawdown'].min()
    market_mdd = df['Market_Drawdown'].min()
    
    # 计算最大回撤日期
    portfolio_mdd_end = df['Portfolio_Drawdown'].idxmin()
    portfolio_mdd_start = df.loc[:portfolio_mdd_end, 'Portfolio_Peak'].idxmax()
    
    # 3. 计算年化收益率
    portfolio_annual_return = (df['Portfolio_Cumulative'].iloc[-1] ** (trading_days / len(df))) - 1
    market_annual_return = (df['Market_Cumulative'].iloc[-1] ** (trading_days / len(df))) - 1
    
    # 4. 计算年化波动率
    portfolio_volatility = df.iloc[:, 0].std() * np.sqrt(trading_days)
    market_volatility = df.iloc[:, 1].std() * np.sqrt(trading_days)
    
    # 5. 计算夏普比率（年化）
    # 将年化无风险利率转换为日利率
    daily_rf = (1 + risk_free_rate) ** (1/trading_days) - 1
    
    portfolio_sharpe = np.sqrt(trading_days) * (df.iloc[:, 0].mean() - daily_rf) / df.iloc[:, 0].std()
    market_sharpe = np.sqrt(trading_days) * (df.iloc[:, 1].mean() - daily_rf) / df.iloc[:, 1].std()
    
    # 6. 计算Sortino比率（考虑下行风险）
    downside_returns = df.iloc[:, 0][df.iloc[:, 0] < daily_rf] - daily_rf
    portfolio_sortino = np.sqrt(trading_days) * (df.iloc[:, 0].mean() - daily_rf) / downside_returns.std()
    
    downside_returns_mkt = df.iloc[:, 1][df.iloc[:, 1] < daily_rf] - daily_rf
    market_sortino = np.sqrt(trading_days) * (df.iloc[:, 1].mean() - daily_rf) / downside_returns_mkt.std()
    
    # 7. 计算Calmar比率（年化收益/最大回撤）
    portfolio_calmar = portfolio_annual_return / abs(portfolio_mdd) if portfolio_mdd != 0 else np.nan
    market_calmar = market_annual_return / abs(market_mdd) if market_mdd != 0 else np.nan
    
    # 打印关键指标
    print("\n" + "="*60)
    print(f"{portfolio_name} VS {market_name} 回测结果")
    print("="*60)
    print(f"回测期间: {df.index[0].strftime('%Y-%m-%d')} 至 {df.index[-1].strftime('%Y-%m-%d')} ({len(df)}个交易日)")
    print("\n关键指标对比:")
    print(f"{'指标':<15} | {portfolio_name:<15} | {market_name}")
    print(f"{'-'*45}")
    print(f"{'年化收益率':<15} | {portfolio_annual_return:.2%} | {market_annual_return:.2%}")
    print(f"{'年化波动率':<15} | {portfolio_volatility:.2%} | {market_volatility:.2%}")
    print(f"{'夏普比率':<15} | {portfolio_sharpe:.2f} | {market_sharpe:.2f}")
    print(f"{'索提诺比率':<15} | {portfolio_sortino:.2f} | {market_sortino:.2f}")
    print(f"{'卡玛比率':<15} | {portfolio_calmar:.2f} | {market_calmar:.2f}")
    print(f"{'最大回撤':<15} | {portfolio_mdd:.2%} ({portfolio_mdd_start.strftime('%Y-%m-%d')} 至 {portfolio_mdd_end.strftime('%Y-%m-%d')}) | {market_mdd:.2%}")
    print(f"{'累计收益率':<15} | {(df['Portfolio_Cumulative'].iloc[-1] - 1):.2%} | {(df['Market_Cumulative'].iloc[-1] - 1):.2%}")
    print("="*60 + "\n")
    
    # 8. 可视化 - 创建图形
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), sharex=True, gridspec_kw={'height_ratios': [2, 1]})
    
    # 累计收益曲线
    ax1.plot(df.index, df['Portfolio_Cumulative'], label=portfolio_name, linewidth=2.5)
    ax1.plot(df.index, df['Market_Cumulative'], label=market_name, linewidth=2.5, alpha=0.8, linestyle='--')
    ax1.set_title(f'{portfolio_name} VS {market_name} - 累计收益率', fontsize=15)
    ax1.set_ylabel('累计收益率', fontsize=12)
    ax1.legend(loc='best')
    ax1.yaxis.set_major_formatter(PercentFormatter(1))
    
    # 添加网格
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # 回撤曲线
    ax2.plot(df.index, df['Portfolio_Drawdown'], label=portfolio_name, linewidth=1.5, color='tab:blue')
    ax2.plot(df.index, df['Market_Drawdown'], label=market_name, linewidth=1.5, color='tab:orange', alpha=0.7)
    
    # 填充回撤区域
    ax2.fill_between(df.index, df['Portfolio_Drawdown'], 0, color='tab:blue', alpha=0.1)
    ax2.fill_between(df.index, df['Market_Drawdown'], 0, color='tab:orange', alpha=0.1)
    
    # 标记最大回撤
    ax2.axhline(y=portfolio_mdd, color='red', linestyle='--', alpha=0.7, 
                label=f'{portfolio_name}最大回撤: {-portfolio_mdd:.1%}')
    ax2.set_title(f'{portfolio_name} VS {market_name} - 回撤曲线', fontsize=15)
    ax2.set_ylabel('回撤幅度', fontsize=12)
    ax2.set_xlabel('日期', fontsize=12)
    ax2.legend(loc='lower right')
    ax2.yaxis.set_major_formatter(PercentFormatter(1))
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    # 设置x轴日期格式
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator())
    
    # 美化布局
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.1)
    
    # 保存图片
    plt.savefig(f'Portfolio_Analysis_{portfolio_name.replace(" ", "_")}.png', dpi=300)
    
    # 显示图形
    plt.show()
    
portfolio_analysis(result_df)    
    
#————————————————————————————————————————————————————————————————