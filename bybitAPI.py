import pprint
from pprint import pprint
import config
from pybit import usdt_perpetual
import logging


url_testnet = 'https://api-testnet.bybit.com'
base_url = 'https://api.bybit.com'

session_auth = usdt_perpetual.HTTP(
    endpoint=base_url,
    api_key=config.bybit_apiKey,
    api_secret=config.bybit_secretKey
)
symbol = 'ETHUSDT'
amount = 0.01

def check_open_position():
    list_of_orders = []
    for position in session_auth.my_position(symbol=symbol)['result']:
        if position['size'] > 0:
            return position

def check_stop_loss(open_position,symbol, side, entry_price, percent):
    if open_position['stop_loss'] == int(entry_price * percent):
        print("Stop loss is set up")
    else:
        session_auth.set_trading_stop(
            symbol=symbol,
            side=side,
            stop_loss=int(entry_price * percent),
            p_r_qty=amount
        )

# print(session_auth.get_conditional_order(symbol= symbol)['result']['data'])
def get_price_conditional_orders():
    list_of_prices_orders = []
    for order in session_auth.get_conditional_order(symbol=symbol)['result']['data']:
        if order['order_status'] == 'Untriggered':
            list_of_prices_orders.append(order['trigger_price'])
    print('get_price_conditional_orders: ', list_of_prices_orders)
    return list_of_prices_orders


def get_stop_order_list():
    stop_order_list = []
    orders = session_auth.get_conditional_order(symbol=symbol)['result']['data']
    for item in orders:
        print(item)
        if item['order_status'] == 'Untriggered':
            return item

def cancel_conditional_order(symbol):
    return session_auth.cancel_all_conditional_orders(symbol=symbol)


def set_up_stop_loss(open_position, entry_price, symbol, side, stop_loss, trailing_stop):
    try:
        if open_position['stop_loss'] == int(entry_price * stop_loss):
            print("Stop loss is set up")
        else:
            print("Make a new one SL")
            session_auth.set_trading_stop(
                symbol=symbol,
                side=side,
                stop_loss=stop_loss,
                trailing_stop=trailing_stop
            )
    except:
        pass


'''cash = 250
i = 0

for i in range(365):
    i +=1
    cash += (cash * 0.01)
    print("Day: ", i, ' cash: ', int(cash), "profit: ", int(round(cash*0.01,2)))'''

