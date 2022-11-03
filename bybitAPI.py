import pprint
from pprint import pprint
import config
from pybit import usdt_perpetual
import logging

from ByBitBot import open_position, actual_bid_price, leverage

url_testnet = 'https://api-testnet.bybit.com'
base_url = 'https://api.bybit.com'

session_auth = usdt_perpetual.HTTP(
    endpoint=base_url,
    api_key=config.bybit_apiKey,
    api_secret=config.bybit_secretKey
)
symbol = 'ETHUSDT'
amount = 0.01

def place_conditional_order(symbol, side, qty, base_price, stop_px):
    return session_auth.place_conditional_order(
        symbol=symbol,
        order_type="Market",
        side=side,
        qty=qty,
        base_price=base_price,
        stop_px=stop_px,
        time_in_force="GoodTillCancel",
        trigger_by="LastPrice",
        reduce_only=False,
        close_on_trigger=False
    )

def get_conditional_order(symbol):
    list_of_side_orders = []
    for order in session_auth.get_conditional_order(symbol= symbol)['result']['data']:
        if order['order_status'] == 'Untriggered':
           list_of_side_orders.append(order['side'])
    print("Conditional orders: ", list_of_side_orders)
    return list_of_side_orders

def check_stop_losses():
    print("Stop Loss= ", open_position['stop_loss'])
    print("Trailing stop loss= ", open_position['trailing_stop'])

def checking_stop_loss(side, angle_bracket, plus_or_minus, leverage):
    if open_position['side'] == side:
        # Set up a new stop loss for POSITION
        print(f"\n ================ Check a stop loss for {side} postion ================")
        print(f'open {side}_position: ', open_position)
        entry_price = open_position['entry_price']
        print(f'{side} entry_price: ', entry_price)
        print("actual profit: ", float(round(entry_price / actual_bid_price) - 1), 2)
        print("stop loss of open position", open_position['stop_loss'])

        # Counting a profit regardless of leverage
        if eval(f"actual_bid_price {angle_bracket} int(entry_price {plus_or_minus} (entry_price * 0.01 / {leverage}))"):
            print("profit higher than 1%")
            # Check the price of stop loss
            print('1% Stop Loss= ', eval(f'int(entry_price {plus_or_minus} (entry_price * 0.01 / {leverage}))')
                  )
            # Set up stop loss
            set_up_stop_loss(open_position, entry_price, symbol, side,
                                      stop_loss=eval(f'round(float(entry_price {plus_or_minus} (entry_price * 0.01 / {leverage})),2)'),
                                      trailing_stop=eval('round(float(entry_price * 0.005 / {leverage}), 2)')
                                      )
            check_stop_losses()
        elif eval(f'actual_bid_price {angle_bracket} int(entry_price {plus_or_minus} (entry_price * 0.005 / {leverage}))'):
            print("profit higher than 0,5%")
            # Check the price of stop loss
            print("0,5% stop loss= ", eval('int(entry_price {plus_or_minus} (entry_price * 0.005 / {leverage}))'))
            # Set up stop loss
            set_up_stop_loss(open_position, entry_price, symbol, side,
                             stop_loss=eval(
                                 f'round(float(entry_price {plus_or_minus} (entry_price * 0.005 / {leverage})),2)'),
                             trailing_stop=eval('round(float(entry_price * 0.005 / {leverage}), 2)')
                             )
            check_stop_losses()
        else:
            set_up_stop_loss(open_position, symbol, side, stop_loss=entry_price + 1,
                                      trailing_stop=eval('round(float(entry_price * 0.01 / {leverage}), 2)')
                                      )
            check_stop_losses()

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

'''def check_stop_loss(open_position,symbol, side, entry_price, percent):
    if open_position['stop_loss'] == int(entry_price * percent):
        print("Stop loss is set up")
    else:
        session_auth.set_trading_stop(
            symbol=symbol,
            side=side,
            stop_loss=int(entry_price * percent),
            p_r_qty=amount
        )'''

# print(session_auth.get_conditional_order(symbol= symbol)['result']['data'])
def get_price_conditional_orders():
    list_of_prices_orders = []
    for order in session_auth.get_conditional_order(symbol=symbol)['result']['data']:
        if order['order_status'] == 'Untriggered':
            list_of_prices_orders.append(order['trigger_price'])
    print('get_price_conditional_orders: ', list_of_prices_orders)
    return list_of_prices_orders


'''def get_stop_order_list():
    stop_order_list = []
    orders = session_auth.get_conditional_order(symbol=symbol)['result']['data']
    for item in orders:
        print(item)
        if item['order_status'] == 'Untriggered':
            return item'''

def cancel_conditional_order(symbol):
    return session_auth.cancel_all_conditional_orders(symbol=symbol)




'''cash = 250
i = 0

for i in range(365):
    i +=1
    cash += (cash * 0.01)
    print("Day: ", i, ' cash: ', int(cash), "profit: ", int(round(cash*0.01,2)))'''

