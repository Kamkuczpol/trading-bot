import time
import ccxt
import config
import bybitAPI
from pybit import usdt_perpetual


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

# ========= connect with exchange ========
exchange = ccxt.bybit({
    'apiKey': config.bybit_apiKey,
    'secret': config.bybit_secretKey,
    'enableRateLimit': True
})

session_auth = usdt_perpetual.HTTP(
    endpoint='https://api.bybit.com',
    api_key=config.bybit_apiKey,
    api_secret=config.bybit_secretKey
)

symbol = 'ETHUSDT'
amount = 0.01
leverage = 5


# print('CCXT Version:', ccxt.__version__)
# exchange.verbose = True

while True:

    #================ fetch the actual price of coin ================
    print("\n\n======>>>> fetch the actual price of coin")
    price = exchange.fetch_ticker(symbol)
    actual_bid_price = float(price['bid'])
    print('actual bid price: ', actual_bid_price)

    #================ fetch the bars ================
    print("\n\n================ fetch the bars ================")
    ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=8)

    #================ find the open position ================
    print("Check the open position")
    open_position = bybitAPI.check_open_position()
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

    #================ find the last lowest price ================
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
    short_stop_loss = int(round(short_price * 1.0066, 2))
    print("\nshort stop loss price: ", short_stop_loss)

    #================check open short position================
    print("================ check open short position ================")
    try:
        if open_position is not None:
            if open_position['side'] == 'Sell':
                #Set up a new stop loss for SHORT POSITION
                print("\n ================ Check a stop loss for SHORT POSITION ================")
                print('open short_position: ', open_position)
                short_entry_price = open_position['entry_price']
                print('short entry_price: ', short_entry_price)
                print('actual_bid_price: ', actual_bid_price)
                print("actual percent: ", float(round(short_entry_price / actual_bid_price) - 1), 2)
                print("stop loss of open position", open_position['stop_loss'])

                # We count a profit regardless of leverage
                if actual_bid_price < int(short_entry_price - (short_entry_price * 0.01 / leverage)):
                    print("profit higher than 1%")
                    print( '1% Stop Loss= ', int(short_entry_price - (short_entry_price * 0.01 / leverage))
                           )
                    bybitAPI.set_up_stop_loss(open_position, short_entry_price, symbol, "Sell",
                                              stop_loss=int(short_entry_price - (short_entry_price * 0.01 / leverage)))
                    check_stop_losses()
                elif actual_bid_price < int(short_entry_price - (short_entry_price * 0.005 / leverage)):
                    print("profit higher than 0,5%")
                    print("0,5% stop loss= ", int(short_entry_price - (short_entry_price * 0.005 / leverage)))
                    bybitAPI.set_up_stop_loss(open_position, short_entry_price, symbol, "Sell",
                                              stop_loss=int(short_entry_price - (short_entry_price * 0.005 / leverage)),
                                              trailing_stop=int(short_entry_price*0.005/leverage))
                    check_stop_losses()
                else:
                    bybitAPI.set_up_stop_loss(open_position, symbol, "Sell", stop_loss=short_stop_loss+1,
                                              trailing_stop=int(short_entry_price*0.005/leverage))
                    check_stop_losses()
        elif "Sell" not in get_conditional_order(symbol):
            try:
                print(" make a new order")
                place_conditional_order(symbol, "Sell", amount, short_price + 1, short_price)
            except:
                print("There was error with get_conditional_order's function")
        elif "Sell" in get_conditional_order(symbol):
            try:
                if short_price not in bybitAPI.get_price_conditional_orders():
                    print("Make a conditional order with a new price")
                    bybitAPI.cancel_conditional_order(symbol)
                    place_conditional_order(symbol=symbol, side="Sell", qty=amount, base_price=short_price + 1,
                                        stop_px=short_price)
                else:
                    pass
            except:
                print("No need to change SL of Short order or there was error")
        else:
            pass
    except:
        print("THere was an error with check position or order")

    # ================ LONG POSITION: find the last highest price ================
    print("================ LONG POSITION: find the last highest price ================")
    the_highest_price = []
    high_price = []

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

    # create a stop loss
    long_stop_loss = int(long_price * 0.999)
    print("\n long_stop_loss: ", long_stop_loss)

    print("================ Open Long position ================")
    # check open long position

    try:
        if open_position is not None:
            if open_position['side'] == 'Buy':
                # Set up a new stop loss for SHORT POSITION
                print("\n ================ Check a stop loss for LONG POSITION ================")
                print('open LONG position: ', open_position)
                long_entry_price = open_position['entry_price']
                print('long entry_price: ', long_entry_price)
                print('actual_bid_price: ', actual_bid_price)
                print("actual percent: ", float(round(long_entry_price / actual_bid_price) - 1), 2)
                print("stop loss of open position", open_position['stop_loss'])

                # We count a profit regardless of leverage
                if actual_bid_price > int(long_entry_price + (long_entry_price * 0.01 / leverage)):
                    print("profit higher than 1%")
                    print('1% Stop loss= ', int(long_entry_price + (long_entry_price * 0.01 / leverage))
                          )
                    bybitAPI.set_up_stop_loss(open_position, long_entry_price, symbol, "Buy",
                                              stop_loss=int(long_entry_price + (long_entry_price * 0.01 / leverage))
                                              )
                    check_stop_losses()

                elif actual_bid_price > int(long_entry_price + (long_entry_price * 0.005 / leverage)):
                    print("profit higher than 0,5%")
                    print("0,5% stop loss= ", int(long_entry_price + (long_entry_price * 0.005 / leverage))
                          )
                    bybitAPI.set_up_stop_loss(open_position, long_entry_price, symbol, "Buy",
                                              stop_loss=int(long_entry_price + (long_entry_price * 0.005 / leverage)),
                                              trailing_stop=int(long_entry_price * 0.005 / leverage)
                                              )
                    check_stop_losses()
                else:
                    session_auth.set_trading_stop(
                        symbol=symbol,
                        side= "Buy",
                        stop_loss=int(long_entry_price - 1),
                        trailing_stop=int(long_entry_price * 0.005 / leverage)
                    )

                    check_stop_losses()
        # checking if there is open long order
        elif "Buy" not in get_conditional_order(symbol):
            try:
                print(" make a new LONG order")
                place_conditional_order(symbol, "Buy", amount, long_price - 1, long_price)
            except:
                print("There was error with get_conditional_order's function")
        elif "Buy" in get_conditional_order(symbol):
            try:
                if long_price not in bybitAPI.get_price_conditional_orders():
                    print("Make a conditional order with a new price")
                    bybitAPI.cancel_conditional_order(symbol)
                    place_conditional_order(symbol=symbol, side="Buy", qty=amount, base_price=long_price - 1,
                                            stop_px=long_price)
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


# Co już próbowałem
#    place conditional order + set trading stop
#    Full  tp_sl_mode nie działa
# replace_conditional_order z stop_order_id też nie działa.
# replace_conditional_order
# Nie moge cancel stop loss, bo nie mam id
# nie mogę replace bo też nie mam id
# Mógłbym zrobić full, potem zrobić cancel, przez trading-stop, a potem ustawić nowe.
