import time
import ccxt
import config
import functions
from pybit import usdt_perpetual

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
leverage = 5


# print('CCXT Version:', ccxt.__version__)
# exchange.verbose = True

while True:
    #================ fetch the actual price of coin ================
    print("\n\n======>>>> Fetch the actual price of coin")
    price = exchange.fetch_ticker(symbol)
    actual_bid_price = float(price['bid'])
    print('actual bid price: ', actual_bid_price)

    #================ fetch the bars ================
    print("\n\n================ Fetch the bars ================")
    ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=8)

    #================ find the open position ================
    print("Check the open position")
    open_position = functions.check_open_position()
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
    if len(functions.get_conditional_order(symbol)) > 2:
        print(session_auth.cancel_all_conditional_orders(symbol=symbol
        ))
    else:
        print("No conditional orders")

    # ================ Check actual price ================
    print('actual_bid_price: ', actual_bid_price)

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

    # Check open short position
    print("================ check open short position ================")
    try:
        if open_position is not None:
            functions.checking_stop_loss("Side", "<", "-", leverage)

        # Place a conditional order
        elif "Sell" not in functions.get_conditional_order(symbol):
            try:
                print(" make a new order")
                functions.place_conditional_order(symbol, "Sell", amount, short_price + 1, short_price)
            except:
                print("There was error with get_conditional_order's function")
        # Change SL of Short order if price changed
        elif "Sell" in functions.get_conditional_order(symbol):
            try:
                if short_price not in functions.get_price_conditional_orders():
                    functions.cancel_conditional_order(symbol)
                    functions.place_conditional_order(symbol=symbol, side="Sell", qty=amount, base_price=short_price + 1,
                                                            stop_px=short_price)
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
            functions.checking_stop_loss("Buy", ">", "+", leverage)
        # Checking if there is open long order
        elif "Buy" not in functions.get_conditional_order(symbol):
            try:
                print(" make a new LONG order")
                functions.place_conditional_order(symbol, "Buy", amount, long_price - 1, long_price)
            except:
                print("There was error with get_conditional_order's function")
        elif "Buy" in functions.get_conditional_order(symbol):
            try:
                if long_price not in functions.get_price_conditional_orders():
                    print("Make a conditional order with a new price")
                    functions.cancel_conditional_order(symbol)
                    functions.place_conditional_order(symbol=symbol, side="Buy", qty=amount, base_price=long_price - 1,
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
