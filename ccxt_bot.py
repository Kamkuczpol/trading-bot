# TODO 1 check if I can take more bars with another exchange

import ccxt, pprint, time, sys
import config
from datetime import datetime
import plotly.graph_objects as go
import calendar
import pandas as pd

check_order_frequency = 0
closed_order_satus = "closed"
symbol= 'ETH/USDT'
traded_amount = 0.001

# pprint.pp(ccxt.exchanges)
# exchange = ccxt.kucoin()

exchange = ccxt.indodax({
    'apiKey': config.indodax_apikey,
    'secret': config.indodax_secretkey
})

exchange.enableRateLimit = True

binance = ccxt.binance({
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',  # ←-------------- quotes and 'future'
    },
    'apiKey': config.binance_apiKey,
    'secret': config.binance_secret,
})

binance.set_sandbox_mode(True)


trading_pair = 'BTC/IDR'

binance_bar = binance.fetch_ohlcv(limit=8, symbol="ETHBUSD", timeframe="1h")

# ================ find the last lowest price ================
the_lowest_price = []
list_low_prices = []

print("\n\n The loop for low  prices")
for line in binance_bar[::-1]:
    list_low_prices.append(line[3])
print("List of the low prices: ", list_low_prices)

for i in range (len(list_low_prices)-1):
    try:
        if list_low_prices[i] > list_low_prices[i+1] and list_low_prices[i+1] < list_low_prices[i+2]:
            the_lowest_price.append(list_low_prices[i+1])
    except IndexError:
        if list_low_prices[i] > list_low_prices[i+1]:
            the_lowest_price.append(list_low_prices[i+1])
print("The lowest price: ", the_lowest_price[0])
low_buy_price = the_lowest_price[0]-1

# ================ find the last highest price ================
the_highest_price = []
list = []

print("\n\n The loop for highest prices")
for line in binance_bar[::-1]:
    list.append(line[2])
print("the highest prices: ", list)

for i in range(len(list) - 1):
    try:
        if list[i] < list[i + 1] and list[i + 1] > list[i + 2]:
            the_highest_price.append(list[i + 1])
    except IndexError:
        if list[i] < list[i + 1]:
            the_highest_price.append(list[i + 1])
print("the_highest_price: ", the_highest_price[0])
price_for_buy = the_highest_price[0]+1

# TODO: ================ make an BUY order ================
binance.set_leverage(5, symbol=symbol)
binance.create_limit_order(symbol,side='buy', amount=0.001, price=price_for_buy)


# TODO: ================ make an SELL order ================

# UWAGA DZIAłA
# exchange.create_limit_order('PAXG/IDR', 'buy', 0.08193233, ask_price)
# pprint.pprint(exchange.fetch_ticker('PAXG/IDR'))


"""
print(exchange.fetch_balance())

# sell one ฿ for market price and receive $ right now
print(kucoin.id, kucoin.create_market_sell_order('BTC/USDT', 0.01))

# limit buy BTC/EUR, you pay €2500 and receive ฿1  when the order is closed
print(kucoin.id, kucoin.create_limit_buy_order('BTC/EUR', 1, 2500.00))

# pass/redefine custom exchange-specific order params: type, amount, price, flags, etc...
kucoin.create_market_buy_order('BTC/USD', 1, {'trading_agreement': 'agree'})
"""