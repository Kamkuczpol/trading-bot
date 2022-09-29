import time
import ccxt
from pybit import usdt_perpetual
import config


def check_open_position():
    list_of_orders = []
    for position in session_auth.my_position(symbol=symbol)['result']:
        if position['size'] > 0:
            return position
def place_conditional_order(symbol, side, qty, base_price, stop_px, take_profit):
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
        close_on_trigger=False,
        take_profit=take_profit
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

def checking_open_position(side, angle_bracket, plus_or_minus, leverage):
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
                                      trailing_stop=round(float(entry_price * 0.01 / leverage), 2)
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
                             trailing_stop=round(float(entry_price * 0.01 / leverage), 2)
                             )
            check_stop_losses()
        else:
            set_up_stop_loss(open_position, symbol, side, stop_loss=entry_price + 1,
                                      trailing_stop=round(float(entry_price * 0.01 / leverage), 2)
                                      )
            check_stop_losses()


def get_price_conditional_orders():
    list_of_prices_orders = []
    for order in session_auth.get_conditional_order(symbol=symbol)['result']['data']:
        if order['order_status'] == 'Untriggered':
            list_of_prices_orders.append(order['trigger_price'])
    print('get_price_conditional_orders: ', list_of_prices_orders)
    return list_of_prices_orders

def cancel_conditional_order(symbol):
    return session_auth.cancel_all_conditional_orders(symbol=symbol)


# ========= connect with exchange ========
exchange = ccxt.bybit({
    'apiKey': config.bybit_apiKey,
    'secret': config.bybit_secretKey,
    'enableRateLimit': True
})
exchange.options['adjustForTimeDifference'] = True

session_auth = usdt_perpetual.HTTP(
    endpoint='https://api.bybit.com',
    api_key=config.bybit_apiKey,
    api_secret=config.bybit_secretKey
)

symbol = 'ETHUSDT'
amount = 0.01
leverage = 1


# print('CCXT Version:', ccxt.__version__)
# exchange.verbose = True

while True:
    #================ Fetch the actual price of coin ================
    print("\n\n======>>>> Fetch the actual price of coin")
    price = exchange.fetch_ticker(symbol)
    actual_bid_price = float(price['bid'])
    print('actual bid price: ', actual_bid_price)

    #================ Fetch the bars ================
    print("\n\n================ Fetch the bars ================")
    ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=8)

    #================ Find the open position ================
    print("Check the open position")
    open_position = check_open_position()
    print('open_position: ', open_position)

    #================ check if position is in Full ================
    print("Check if position is in a Full mode")
    try:
        if open_position['tp_sl_mode'] != "Full":
            session_auth.full_partial_position_tp_sl_switch(
                symbol=symbol,
                tp_sl_mode="Full"
            )
        else:
            print('Open position is in Full mode')
    except TypeError:
        print('pass type error')

    # ================ Check if number of orders is bigger than 2 ================
    # if len(get_conditional_order(symbol)) > 2:
    #     print(session_auth.cancel_all_conditional_orders(symbol=symbol
    #     ))
    # else:
    #     print("No conditional orders")

    # ================ Check actual price ================
    print('actual_bid_price: ', actual_bid_price)

    #================ Find the last lowest price ================
    print("\n\n================ find the last lowest price ================ ")
    the_lowest_price = []
    low_prices = []

    for line in ohlcv[::-1]:
        low_prices.append(line[3])
    print("List of the low prices: ", low_prices)

    for i in range(len(low_prices) - 1):
        try:
            if low_prices[i] > low_prices[i + 1] < low_prices[i + 2]:
                the_lowest_price.append(low_prices[i + 1])
            if low_prices[i] < low_prices[i + 1]:
                the_lowest_price.append(low_prices[i])
        except IndexError:
            the_lowest_price.append(low_prices[-1])

    print('the_lowest_prices: ', the_lowest_price)
    print("\nThe lowest price is ", the_lowest_price[0])
    short_price = the_lowest_price[0] - 1
    print("\nSHORT PRICE is ", short_price)

    # Check open short position
    print("================ check open short position ================")
    try:
        if open_position is not None:
            checking_open_position("Sell", "<", "-", leverage)
        # Place a conditional order
        elif "Sell" not in get_conditional_order(symbol):
            try:
                print(" make a new order")
                place_conditional_order(symbol, "Sell", amount, short_price + 1, short_price,
                                        take_profit=float(round(short_price - (short_price*0.01/leverage),2))
                                        )
            except:
                print("There was error with get_conditional_order's function")
        # Change SL of Short order if price changed
        elif "Sell" in get_conditional_order(symbol):
            try:
                if short_price not in get_price_conditional_orders():
                    cancel_conditional_order(symbol)
                    place_conditional_order(symbol=symbol,
                                            side="Sell",
                                            qty=amount,
                                            base_price=short_price + 1,
                                            stop_px=short_price,
                                            take_profit=float(round(short_price - (short_price*0.01/leverage),2)))
                else:
                    pass
            except:
                print("No need to change SL of Short order or there was error")
        else:
            pass
    except:
        print("There was an error with check position or order")

    # Find the last highest price for Long Position
    print("================ LONG POSITION: find the last highest price ================")
    the_highest_price = []
    high_price = []

    #Loop to find the highest position
    print("\n\nThe loop for highest prices")
    for line in ohlcv[::-1]:
        high_price.append(line[2])
    print("\nthe highest prices: ", high_price)

    for i in range(len(high_price) - 1):
        try:
            if high_price[i] > high_price[i + 1]:
                the_highest_price.append(high_price[i])
            elif high_price[i] < high_price[i + 1] > high_price[i + 2]:
                the_highest_price.append(high_price[i + 1])
        except IndexError:
            if high_price[i] < high_price[i + 1]:
                the_highest_price.append(high_price[i + 1])

    print("\n The_highest_price: ", the_highest_price[0])
    long_price = the_highest_price[0] + 1
    print("\n LONG PRICE: ", long_price)

    print("================ Open Long position ================")
    # check open long position
    try:
        if open_position is not None:
            checking_open_position("Buy", ">", "+", leverage)
        # Checking if there is open long order
        elif "Buy" not in get_conditional_order(symbol):
            try:
                print(" make a new LONG order")
                place_conditional_order(symbol, "Buy", amount, long_price - 1, long_price,
                                        take_profit=float(round(long_price + (long_price*0.01/leverage),2))
                                        )
            except:
                print("There was error with get_conditional_order's function")
        elif "Buy" in get_conditional_order(symbol):
            try:
                if long_price not in get_price_conditional_orders():
                    print("Make a conditional order with a new price")
                    cancel_conditional_order(symbol)
                    place_conditional_order(symbol=symbol,
                                            side="Buy",
                                            qty=amount,
                                            base_price=long_price - 1,
                                            stop_px=long_price,
                                            take_profit=float(round(long_price + (long_price*0.01/leverage),2))
                                            )
                else:
                    pass
            except:
                print("No need to change SL of Short order or there was error")
        else:
            pass
    except:
        print("There was error with long order or position")
    print("Break for 1 second")
    time.sleep(1)
