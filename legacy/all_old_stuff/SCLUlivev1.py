import time
import os
import pandas as pd
from kiteconnect import KiteConnect
import datetime as dt
import time
cwd = os.chdir('/Users/anishrayaguru/Desktop/SCLU')

#os.system('{} {}'.format('python3', './mayankdls/access_token_gen.py'))

access_token = open("access_token.txt", 'r').read()
key_secret = open("api_key.txt", 'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

#list the number of underlyings and their corresponding instrument tokens- url of kite pagaes
instrument_tokens = [10716162,10684418]
no_underlyings = len(instrument_tokens)

instrument_dump = kite.instruments("NFO")
instrument_df = pd.DataFrame(instrument_dump)
instrument_df.to_csv("instrumentdump.csv",index=False)

def instrumentLookup(instrument_df,token):
    #finds instrument symbol
    try:
        return instrument_df[instrument_df.instrument_token==token].tradingsymbol.values[0]
    except:
        print("wrong instrument token given")

instrument_symbols = list()
count = 0
for i in instrument_tokens:
    instrument_symbols.append(instrumentLookup(instrument_df, i))
print("instrument symbols are-")
print(instrument_symbols)
intrade = list()
for i in range(no_underlyings):
    intrade.append(False)

def fetchOHLC(duration, instrument_token):
    #global instrument_token
    """extracts historical data and outputs in the form of dataframe"""
    data = pd.DataFrame(kite.historical_data(instrument_token,dt.datetime.now()-dt.timedelta(minutes = 3*duration), 
    dt.datetime.now(),'3minute', oi = True))
    data.set_index("date",inplace=True)
    return data

def oideriv(dfi):
    dfi['doi'] = None
    dfi['d2oi'] = None

    for i in range(1,len(dfi)):
        dfi.iloc[i,6] = round((dfi.iloc[i,5] - dfi.iloc[i-1,5])/3)
        if i > 1:
            dfi.iloc[i,7] = round((dfi.iloc[i,5] + dfi.iloc[i-2,5] - (2*dfi.iloc[i-1,5]))/9)
    return dfi

no_trades = 0
tradelimit = 30
def placeMarketOrder(instrument_symbol,buy_sell,quantity):    
    # Place an intraday market order on NSE
    global no_trades
    if no_trades < (2*tradelimit):
        no_trades += 1
        if buy_sell == "buy":
            t_type=kite.TRANSACTION_TYPE_BUY
        elif buy_sell == "sell":
            t_type=kite.TRANSACTION_TYPE_SELL   
        kite.place_order(tradingsymbol=instrument_symbol,
                        exchange=kite.EXCHANGE_NFO,
                        transaction_type=t_type,
                        quantity=quantity,
                        order_type=kite.ORDER_TYPE_MARKET,
                        product=kite.PRODUCT_MIS,
                        variety=kite.VARIETY_REGULAR)

def main(pos, sens, feel, instrument_token, lot_size,instrument_name, lots = 1):
    global intrade
    global instrument_symbols
    try:
        df = fetchOHLC(5, instrument_token)
        df = oideriv(df)
        #print(df.iloc[-1:,5:])
        #feel = Decimal(feel)
        if intrade[pos-1] == False:
            if df.iloc[-1,6] < 0 and df.iloc[-1,7] < ((-1*sens*feel)//(10*100)):
                #placeMarketOrder(instrument_symbols[pos-1], "buy", lots*lot_size)
                print(instrument_name," unwind around-", df.iloc[-1,3])
                intrade[pos-1] = True
        else:
            if df.iloc[-1,6] > ((-1*sens*feel)//(100)) or df.iloc[-1,7] > ((-1*sens*feel)//(10*100)):
                #placeMarketOrder(instrument_symbols[pos-1], "sell", lots*lot_size)
                if df.iloc[-1,6] > -10*sens*feel:
                    print("first derivative exit")
                elif df.iloc[-1,7] > -sens*feel:
                    print("second derivative exit")
                print(instrument_name," unwind stopped at around-", df.iloc[-1,3])
                intrade[pos-1] = False
    except:
            print("smth went wrong")

# Continuous execution
base_time = time.mktime(time.strptime("09:15:00", "%H:%M:%S"))
x = 180 -((time.time() - base_time)%180) + 13
time.sleep(x)
#time.sleep(27*60)
starttime=time.time()
timeout = time.time() + 60*60*10  # 60 seconds times 60 meaning the script will run for 1 hr *10

while time.time() <= timeout:
    try:
        readable_time = dt.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        print(readable_time)
        #print("passthrough at ",time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        main(1,7, 9*1000000, 10716162, 25, "24000 ce finnifty", 2)
        main(2,7, 5*1000000, 10684418, 25, "23800 pe finnifty", 2)
        

        

        #main() - for the second underlying
        time.sleep(180 - ((time.time() - starttime) % 180.0)) # 180 second interval between each new execution
    except KeyboardInterrupt:
        print('\n\nKeyboard exception received. Exiting.')
        print("bye bye")    
        exit()

