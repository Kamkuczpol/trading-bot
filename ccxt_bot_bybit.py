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
        # price=1652,
        base_price=base_price,
        stop_px=stop_px,
        # stop_loss= stop_loss,
        # tp_sl_mode="Full",
        time_in_force="GoodTillCancel",
        trigger_by="LastPrice",
        reduce_only=False,
        close_on_trigger=False
    )


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
leverage = 3

# print('CCXT Version:', ccxt.__version__)
# exchange.verbose = True


while True:

    # TODO ================ fetch the actual price of coin ================
    print("\n\n======>>>> fetch the actual price of coin")
    price = exchange.fetch_ticker(symbol)
    actual_bid_price = float(price['bid'])
    print('actual bid price: ', actual_bid_price)

    # TODO ================ fetch the bars ================
    print("\n\n================ fetch the bars ================")
    ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=8)

    # TODO ================ find the open position ================
    print("Check the open position")
    open_position = bybitAPI.check_open_position()
    print('open_position: ', open_position)

    # TODO ================ check if position is in Full ================
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

    # TODO ================ find the last lowest price ================
    print("\n\n================ find the last lowest price ================ ")
    the_lowest_price = []
    low_prices = []

    for line in ohlcv[::-1]:
        low_prices.append(line[3])
    print("List of the low prices: ", low_prices)

    for i in range(len(low_prices) - 1):
        try:
            # if low_prices[i] > low_prices[i + 1] < low_prices[i + 2]:
            #     the_lowest_price.append(low_prices[i + 1])
            if low_prices[i] < low_prices[i + 1]:
                the_lowest_price.append(low_prices[i])
        except IndexError:
            the_lowest_price.append(low_prices[-1])

    print("\nThe lowest price is ", the_lowest_price[0])
    short_price = the_lowest_price[0] - 1

    print("\nSHORT PRICE is ", short_price)
    short_stop_loss = int(round(short_price * 1.0066, 2))
    print("\nshort stop loss price: ", short_stop_loss)

    print("================ check open short position ================")
    # TODO: ================check open short position================

    print("Check is open position is SHORT")
    if open_position is not None:
        if open_position['side'] == 'Sell':
            # TODO: Set up a new stop loss for SHORT POSITION
            print("\n ================ TODO: Set up a new stop loss for SHORT POSITION ================")
            print('short_position: ', open_position)
            short_entry_price = open_position['entry_price']
            print('entry_price: ', short_entry_price)
            print('actual_bid_price: ', actual_bid_price)
            print("actual percent: ", float(round(short_entry_price / actual_bid_price) - 1), 2)
            print("1 percent profit with 3 leverage= ",
                  int(short_entry_price * 0.997))
            print("stop loss of open position", open_position['stop_loss'])

            if actual_bid_price < int(short_entry_price * 0.997):
                print("profit higher that 1%")
                bybitAPI.set_up_stop_loss(open_position, short_entry_price,symbol, "Sell", stop_loss=0.997, trailing_stop=0.0041)
                if actual_bid_price < int(short_entry_price - (short_entry_price * 0.005 / leverage)):
                    stop_loss_half_percent = int(short_stop_loss - (short_entry_price * 0.005 / leverage))
                    print("profit higher that 0,5%")
                    bybitAPI.set_up_stop_loss(open_position, short_entry_price,symbol, "Sell", stop_loss=stop_loss_half_percent, trailing_stop=0.0041)
                else:
                    try:
                        session_auth.set_trading_stop(
                            symbol=symbol,
                            side="Sell",
                            stop_loss=int(short_entry_price * 1.0033),
                            p_r_qty=amount
                        )
                    except:
                        pass
    elif "Sell" not in bybitAPI.get_conditional_order(symbol):
        try:
            print(" make a new order")
            # TODO: ================make an SHORT order================
            place_conditional_order(symbol, "Sell", amount, short_price + 1, short_price)
        except:
            print("There was error with get_conditional_order's definition")
    elif "Sell" in bybitAPI.get_conditional_order(symbol):
        if short_price not in bybitAPI.get_price_conditional_orders():
            bybitAPI.cancel_conditional_order(symbol)
            place_conditional_order(symbol=symbol, side="Sell", qty=amount, base_price=short_price + 1,
                                    stop_px=short_price)
    else:
        pass

    # TODO ================ LONG POSITION: find the last highest price ================
    print("================ LONG POSITION: find the last highest price ================")
    the_highest_price = []
    high_price = []

    print("\n\nThe loop for highest prices")
    for line in ohlcv[::-1]:
        high_price.append(line[2])
    print("\nthe highest prices: ", high_price)

    for i in range(len(high_price) - 1):
        try:
            # if high_price[i] > high_price[i + 1]:
            #     the_highest_price.append(high_price[i])
            if high_price[i] < high_price[i + 1] > high_price[i + 2]:
                the_highest_price.append(high_price[i + 1])
        except IndexError:
            if high_price[i] < high_price[i + 1]:
                the_highest_price.append(high_price[i + 1])

    print("\nthe_highest_price: ", the_highest_price[0])
    long_price = the_highest_price[0] + 1
    print("\nLONG PRICE: ", long_price)

    # create a stop loss
    long_stop_loss = int(long_price * 0.993)
    print("\nlong_stop_loss: ", long_stop_loss)

    print("================ Open Long position ================")
    # TODO: check is open long position
    if open_position is not None:
        if open_position['side'] == 'Buy':
            # TODO: Check a new stop loss for LONG POSITION
            print("\n ================ Check a new stop loss for LONG POSITION ================")
            long_entry_price = open_position['entry_price']
            print('entry_price: ', long_entry_price)
            print('actual_bid_price: ', actual_bid_price)

            if actual_bid_price > int(long_entry_price * 1.0034):
                print("profit higher than 1%")
                print("Check stop loss")
                # TODO: Dodać if dla pybit.exceptions.InvalidRequestError: Not modified (ErrCode: 130127)
                bybitAPI.set_up_stop_loss(open_position,
                                      long_entry_price, symbol,
                                      side="Buy",
                                      stop_loss=1.0033,
                                      trailing_stop=0.0041,)
                if actual_bid_price > int(long_entry_price + (long_entry_price * 0.005 / leverage)):
                    long_stop_loss_half_percent = int(long_entry_price - (long_entry_price * 0.005 / leverage))
                    print("profit higher that 0,5%")
                    bybitAPI.set_up_stop_loss(open_position, long_entry_price, symbol, "Buy",
                                              stop_loss=long_stop_loss_half_percent, trailing_stop=0.0041)

                else:
                    bybitAPI.check_stop_loss(open_position, symbol, "Buy", long_entry_price, 0.997)
    # checking if there is open long order
    elif "Buy" not in bybitAPI.get_conditional_order(symbol):
        print("Checking conditional order")
        # place a LONG conditional order
        place_conditional_order(
            symbol=symbol,
            side="Buy",
            qty=amount,
            base_price=long_price - 1,
            stop_px=long_price
        )
    elif "Buy" in bybitAPI.get_conditional_order(symbol):
        if long_price not in bybitAPI.get_price_conditional_orders():
            bybitAPI.cancel_conditional_order(symbol)
            # Change conditional long order
            try:
                place_conditional_order(
                symbol=symbol,
                side="Buy",
                qty=amount,
                base_price=long_price - 1,
                stop_px=long_price,
            )
            except:
                pass
    else:
        pass
    print("Break 2 seconds")
    time.sleep(2)

# TODO: zmniejszyć liczbę requestów, bo się wykrzacza jak mamy dwa otwarte pozycje
# TODO: zrobić warunek dla short stop loss

# Co już próbowałem
#    place conditional order + set trading stop
#    Full  tp_sl_mode nie działa
# replace_conditional_order z stop_order_id też nie działa.
# replace_conditional_order
# Nie moge cancel stop loss, bo nie mam id
# nie mogę replace bo też nie mam id
# Mógłbym zrobić full, potem zrobić cancel, przez trading-stop, a potem ustawić nowe.
