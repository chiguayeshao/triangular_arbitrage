import ccxt
import pandas as pd
import time


def main():
    # 初始化交易所
    binance_exchange = ccxt.binance({
        'timeout': 15000,
        'enableRateLimit': True
    })

    # 加载行情
    markets = binance_exchange.load_markets()

    # step1
    # 选择两个交易市场
    market_a = 'BTC'
    market_b = 'ETH'

    # step2
    # 找到同时以a和b计价的货币
    # 市场内的所有交易对
    symbols = list(markets.keys())

    # 存放到DataFrame()
    symbols_df = pd.DataFrame(data=symbols ,columns=['symbol'])

    # 分割字符串，得到 基础货币/计价货币
    base_quote_df = symbols_df['symbol'].str.split(pat='/', expand=True)
    base_quote_df.columns = ['base', 'quote']

    #过滤得到以a, b计价的计价货币
    base_a_list = base_quote_df[base_quote_df['quote']== market_a]['base'].values.tolist()
    base_b_list = base_quote_df[base_quote_df['quote'] == market_b]['base'].values.tolist()

    #获取相同的基础货币列表
    common_base_list = list(set(base_a_list).intersection(set(base_b_list)))

    # print('{}和{}共有{}个相同的计价货币'.format(market_a,market_b,len(common_base_list)))
    # print(common_base_list)


    #step3执行套利步骤

    #结果保存到DataFrame()中
    columns = [
        'Market A',
        'Market B',
        'Market C',
        'P1',
        'P2',
        'P3',
        'Profit(‰)'
    ]

    result_df = pd.DataFrame(columns=columns)

    #获取前一分钟的close价格
    #现在是模拟，强制计算前一分钟的收盘价
    #实盘的话要计算实时数据
    last_min = binance_exchange.milliseconds() - 60 * 1000

    for base_coin in common_base_list:
        market_c = base_coin
        market_a2b_symbol = '{}/{}'.format(market_b, market_a)
        market_b2c_symbol = '{}/{}'.format(market_c, market_b)
        market_a2c_symbol = '{}/{}'.format(market_c, market_a)

        #获取行情前一分钟的k线数据
        market_a2b_kline = binance_exchange.fetch_ohlcv(market_a2b_symbol, since=last_min, limit=1, timeframe='1m')
        market_b2c_kline = binance_exchange.fetch_ohlcv(market_b2c_symbol, since=last_min, limit=1, timeframe='1m')
        market_a2c_kline = binance_exchange.fetch_ohlcv(market_a2c_symbol, since=last_min, limit=1, timeframe='1m')

        #判空
        if len(market_a2b_kline) == 0 or len(market_b2c_kline) == 0 or len(market_a2c_kline) == 0 :
            continue

        #获取行情前一分钟的交易对价格
        p1 = market_a2b_kline[0][4]
        p2 = market_b2c_kline[0][4]
        p3 = market_a2c_kline[0][4]

        #价差
        profit = (p3 / (p1 * p2) - 1) * 1000

        result_df = result_df.append({
            'Market A': market_a,
            'Market B': market_b,
            'Market C': market_c,
            'P1': p1,
            'P2': p2,
            'P3': p3,
            'Profit(‰)': profit
        }, ignore_index=True)

        #显示信息
        print(result_df.tail(1))

        #防止超过rate limit
        time.sleep((binance_exchange.rateLimit / 1000))

    result_df.to_csv('./tri_arbitrage_results.csv', index=None)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
