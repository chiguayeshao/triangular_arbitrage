# 关于三角套利的理解

## 三角套利的模型

### 图示

### 策略描述

1. 选择两个交易市场AB如（USDT/BTC）
2. 找到同时以A和B计价的货币（如ETH/USDT ， ETH/BTC）
3. 执行套利步骤
4. 根据获利比例选择合适的套利货币

### 举例

1. 现在我需要更多的RMB
2. 恰巧目前的市场可以用100RMB购买100g黄金
3. 又恰巧100g黄金可以购买1瓶茅台
4. 再恰巧卖出1瓶茅台可以获得200RMB

因此在上述过程中，使用了以下三个交易对

- 黄金/RMB （使用RMB购买黄金）
- 茅台/黄金 （使用黄金购买茅台）
-  RMB/茅台 （使用茅台购买RMB，也就是卖出茅台）

### 套利步骤

#### 用数学方式表达

1. 假设我们利用x套利

2. A持仓量： amount_a

   注：如有100RMB

3. 可以买入B的数量： amount_a / price_b

   注：price_b 为 B对A的交易对价格

   如：100g黄金 / 100RMB

4. 可以买入x的数量： (amount_a / price_b) / price_fuck

   注：price_fuck 为x对B的交易对价格

   如100g黄金 / 1瓶茅台

5. 卖出所有x，获得A的数量：((amount_a / price_b) / price_fuck)* price_x

   注：price_x 为x对A的交易对价格

   如：1瓶茅台 / 200RMB

6. 计算得出获利比例：

   ( ((amount_a / price_b) / price_fuck)* price_x - amount_a) / amount_a

   计算得出

   Price_x / (price_b * price_fuck) -1

   举例

   200/（1*100）- 1 =  2

#### 我们的需求

- 找到可以用来套利的货币

#### 注意事项

- 行情获取的过程中，要尽量保证行情的数据是 <b>同一时刻</b> 的

#### 难点

- 同时监控所有适合三角套利的货币
- 在市场上同时成交
- 对交易系统的并发要求高

## 程序实现

### step1

```python
# 初始化交易所
binance_exchange = ccxt.binance({
    'timeout': 15000,
    'enableRateLimit': True
})

# 加载行情
markets = binance_exchange.load_markets()
```

### step2

#### 选择两个交易币种

这里选择 BTC ETH 的原因：

1. BTC 和 ETH 可以组成交易对
2. BTC 和大多数 FUCK 可以组成交易对
3. ETh 和大多数 FUCK 可以组成交易对

```python
# 选择两个交易市场
market_a = 'BTC'
market_b = 'ETH'
```

#### 选择同时可以使用BTC和ETH计价的币种

```python
# 找到币安市场中所有交易对
symbols = list(markets.keys())

# 将找到的交易对存放到DataFrame()
symbols_df = pd.DataFrame(data=symbols ,columns=['symbol'])

#将得到的symbols_df分割成两个部分
#得到基础货币/计价货币
base_quote_df = symbols_df['symbol'].str.split(pat='/', expand=True)
base_quote_df.columns = ['base', 'quote']
#将base_quote_df过滤
#筛选以BTC计价的交易对
base_a_list = base_quote_df[base_quote_df['quote']== market_a]['base'].values.tolist()
#筛选以ETH计价的交易对
base_b_list = base_quote_df[base_quote_df['quote'] == market_b]['base'].values.tolist()

#筛选出既以BTC计价，又以ETH计价的货币，取交集
common_base_list = list(set(base_a_list).intersection(set(base_b_list)))
```

#### 执行套利步骤

```python
#需要将最终结果保存在DataFrame()中
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

#暂时使用模拟数据，计算当前时间前一分钟的市场收盘价格
#如果是实盘的话，我们这里需要修改为实时数据

#切换为前一分钟
last_min = binance_exchange.milliseconds() - 60 * 1000

#遍历之前获得的交集common_base_list
for base_coin in common_base_list:
    market_c = base_coin
    #用货币a买货币b（如BTC买ETH）
    market_a2b_symbol = '{}/{}'.format(market_b, market_a)
    #用货币b买货币c（如ETH买c）
    market_b2c_symbol = '{}/{}'.format(market_c, market_b)
    #将货币c卖出为货币a（如卖出c获得BTC）
    market_a2c_symbol = '{}/{}'.format(market_c, market_a)

    #获取行情前一分钟的k线数据
    #BTC/ETH的k线
    market_a2b_kline = binance_exchange.fetch_ohlcv(market_a2b_symbol, since=last_min, limit=1, timeframe='1m')
    #ETH/c的K线
    market_b2c_kline = binance_exchange.fetch_ohlcv(market_b2c_symbol, since=last_min, limit=1, timeframe='1m')
    #c/BTC的k线
    market_a2c_kline = binance_exchange.fetch_ohlcv(market_a2c_symbol, since=last_min, limit=1, timeframe='1m')

    #判空，防止出现异常，遇到空直接跳过
    if len(market_a2b_kline) == 0 or len(market_b2c_kline) == 0 or len(market_a2c_kline) == 0 :
        continue
		
        #现在是模拟盘，用前一分钟的数据计算
        #获取行情前一分钟的交易对价格
        p1 = market_a2b_kline[0][4]
        p2 = market_b2c_kline[0][4]
        p3 = market_a2c_kline[0][4]

        #计算出收益率
        profit = (p3 / (p1 * p2) - 1) * 1000
		#将所有数据放入之前创造的DataFrame()中
        result_df = result_df.append({
            'Market A': market_a,
            'Market B': market_b,
            'Market C': market_c,
            'P1': p1,
            'P2': p2,
            'P3': p3,
            'Profit(‰)': profit
        }, ignore_index=True)

        #设置api请求间隔，防止超过rate limit被交易所屏蔽
        time.sleep((binance_exchange.rateLimit / 1000))
        
#循环结束，将得到的数据存为csv文件
result_df.to_csv('./tri_arbitrage_results.csv', index=None)

#执行主程序
if __name__ == '__main__':
    main()
```



