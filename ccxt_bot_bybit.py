import time
from pprint import pprint
import ccxt
import config
import bybit
import bybitAPI


# ========= connect with exchange ========
def create_stop_limit_order(symbol, side, amount, short_price, short_stop_loss):
    exchange.create_stop_limit_order(
        symbol=symbol,
        side='sell',
        amount=amount,
        price=short_price,
        stopPrice=short_price,
        params={
            'stop_loss': short_stop_loss,
            'leverage': 3,
            'base_price': short_price,
            'tp_sl_mode': 'Full'
        })

def close_position(symbol, amount, side,):
    exchange.create_order(symbol=symbol,
                          amount=amount,
                          type='Market',
                          side=side,
                          price=actual_bid_price,
                          params={'reduce_only': True})
    return True


exchange = ccxt.bybit({
    'apiKey': config.bybit_apiKey,
    'secret': config.bybit_secretKey,
    'enableRateLimit': True
})

# exchange.load_markets()
symbol = 'ETHUSDT'
amount = 0.01

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
    # pprint(ohlcv[::-1])

    # TODO ================ find the last lowest price ================
    print("\n\n================ find the last lowest price ================ ")
    the_lowest_price = []
    low_prices = []

    for line in ohlcv[::-1]:
        low_prices.append(line[3])
    print("List of the low prices: ", low_prices)

    for i in range(len(low_prices) - 1):
        try:
            if low_prices[i] > low_prices[i + 1] < low_prices[i + 2]:
                the_lowest_price.append(low_prices[i+1])
            elif low_prices[i] < low_prices[i + 1]:
                the_lowest_price.append(low_prices[i])
        except IndexError:
                the_lowest_price.append(low_prices[-1])

    print("\nThe lowest price: ", the_lowest_price[0])
    short_price = int(the_lowest_price[0]) - 1

    print("\nSHORT PRICE: ", short_price)
    short_stop_loss = int(short_price * 1.005)
    print("\nshort stop loss price: ", short_stop_loss)

    # # cancel all not triggered orders
    # bybitAPI.cancel_conditional_order(symbol)

    print("================ open short position ================")
    # TODO: ================check open short position================
    is_open = bybitAPI.check_open_position()
    if 'Sell' in is_open:
        # TODO: Set up a new stop loss for SHORT POSITION
        print("\n ================ TODO: Set up a new stop loss for SHORT POSITION ================")
        short_position = bybitAPI.get_open_positions(symbol, side='Sell')
        print('short_position: ', short_position)
        short_entry_price = short_position['entry_price']
        print('entry_price: ', short_entry_price)
        print('actual_bid_price: ', actual_bid_price)
        print("actual percent: ", round((short_entry_price / actual_bid_price) - 1, 2))
        print("actual_bid_price * 0.997: ", round(actual_bid_price * 0.997, 2))

        # if actual_bid_price < int(round(short_entry_price * 0.985, 2)):
        #     bybitAPI.session_auth.set_trading_stop(
        #         symbol=symbol,
        #         tp_sl_mode='Full',
        #         side="Sell",
        #         stop_loss=int(short_entry_price * 0.986)
        #     )

        # elif actual_bid_price < int(round(short_entry_price * 0.988, 2)):
        #     bybitAPI.session_auth.set_trading_stop(
        #         symbol=symbol,
        #         tp_sl_mode='Full',
        #         side="Sell",
        #         stop_loss=int(short_entry_price * 0.989)
        #     )

        if actual_bid_price < short_entry_price * 0.993:
            bybitAPI.session_auth.set_trading_stop(
                symbol=symbol,
                side="Sell",
                stop_loss=float(round(short_entry_price * 0.993, 2)
                                ))

        elif actual_bid_price < int(short_entry_price * 0.997):
            # bybitAPI.session_auth.set_trading_stop(symbol, "sell", short_entry_price, 0.997)
            bybitAPI.session_auth.set_trading_stop(
                symbol=symbol,
                side="Sell",
                stop_loss=float(round(short_entry_price * 0.997, 2)
                                ))
        else:
            pass

    elif "Sell" not in bybitAPI.get_conditional_order():
        print(" make a new order")
        # TODO: ================make an SHORT order================
        exchange.create_stop_limit_order(
            symbol=symbol,
            side='sell',
            amount=amount,
            price=short_price,
            stopPrice=short_price,
            params={
                'stop_loss': short_stop_loss,
                'leverage': 3,
                'base_price': short_price,
                'tp_sl_mode': 'Full'
            })
    elif "Sell" in bybitAPI.get_conditional_order():
        if short_price not in bybitAPI.get_price_conditional_orders():
            bybitAPI.cancel_conditional_order(symbol)
            exchange.create_stop_limit_order(
                symbol=symbol,
                side="Sell",
                amount=amount,
                price=short_price,
                stopPrice=short_price,
                params={
                    'stop_loss': short_stop_loss,
                    'leverage': 3,
                    'base_price': short_price,
                    'tp_sl_mode': 'Full'
                })
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
            if high_price[i] > high_price[i + 1]:
                the_highest_price.append(high_price[i])
            elif high_price[i] < high_price[i + 1] > high_price[i + 2]:
                the_highest_price.append(high_price[i+1])
        except IndexError:
            if high_price[i] < high_price[i + 1]:
                the_highest_price.append(high_price[i+1])

    print("\nthe_highest_price: ", the_highest_price[0])
    long_price = the_highest_price[0] + 1
    print("\nLONG PRICE: ", long_price)

    # create a stop loss
    long_stop_loss = int(long_price * 0.995)
    print("\nStop loss price: ", long_stop_loss)


    print("================ Open Long position ================")
    # TODO: check is open long position

    is_open = bybitAPI.check_open_position()
    if 'Buy' in is_open:
        # TODO: Check a new stop loss for LONG POSITION
        print("\n ================ Check a new stop loss for LONG POSITION ================")
        long_position = bybitAPI.get_open_positions(symbol, side='Buy')
        print('long_position: ', long_position)
        print(type(long_position))
        long_entry_price = long_position['entry_price']
        print('entry_price: ', long_entry_price)
        print('actual_bid_price: ', actual_bid_price)
        print("actual percent: ", round((long_entry_price / actual_bid_price) - 1, 2))

        if actual_bid_price > int(long_entry_price * 1.0066): # 1664
            # bybitAPI.session_auth.set_trading_stop(symbol=symbol, side="Buy", entry_price=long_entry_price, percent= 1.006)

            bybitAPI.session_auth.set_trading_stop(
                symbol=symbol,
                side="Buy",
                stop_loss=float(round(long_entry_price * 1.006, 2)),
            )

        elif actual_bid_price > int(long_entry_price * 1.003): # 1658
            percent = 1.003
            # bybitAPI.session_auth.set_trading_stop(symbol=symbol, side="Buy", entry_price=long_entry_price, percent=1.003)
            bybitAPI.session_auth.set_trading_stop(
                symbol=symbol,
                side="Buy",
                stop_loss=float(round(long_entry_price * 1.003, 2)
            ))
        else:
            # bybitAPI.set_trading_stop(symbol=symbol, side="Buy", entry_price=long_entry_price, percent= 0.996)
            pass
#pybit.exceptions.InvalidRequestError:  (ErrCode: 130142) (ErrTime: 09:37:10).
    elif "Buy" not in bybitAPI.get_conditional_order():
        # TODO: make a LONG order
        exchange.create_stop_limit_order(
            symbol=symbol,
            side='buy',
            price=long_price,
            stopPrice=long_price,
            amount=amount,
            params={
                'stop_loss': long_stop_loss,
                'leverage': 3,
                'base_price': long_price-1,
                'tp_sl_mode': 'Full'
            })

    elif "Buy" in bybitAPI.get_conditional_order():
        if long_price not in bybitAPI.get_price_conditional_orders():
            bybitAPI.cancel_conditional_order(symbol)
            exchange.create_stop_limit_order(
                symbol=symbol,
                side="Buy",
                price=long_price,
                stopPrice=long_price,
                amount = amount,
                params={
                    'stop_loss': long_stop_loss,
                    'leverage': 3,
                    'base_price': long_price-1,
                    'tp_sl_mode': 'Full'
                })
    else:
        pass

    time.sleep(2)

# TODO: google request time out