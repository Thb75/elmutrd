######################################################################
######################################################################

import tweepy
import datetime
import ccxt
import time
import os
from os import environ


####### TWEEPY AUTH
Twitter_API_KEY = environ['Twitter_API_KEY']
Twitter_API_secret_key = environ['Twitter_API_secret_key']
Twitter_Access_token = environ['Twitter_Access_token']
Twitter_Access_secret_token = environ['Twitter_Access_secret_token']

auth = tweepy.OAuthHandler(Twitter_API_KEY, 
    Twitter_API_secret_key)
auth.set_access_token(Twitter_Access_token, 
    Twitter_Access_secret_token)
api = tweepy.API(auth)
######################

####### CCXT BINANCE AUTH
#hitbtc = ccxt.hitbtc()
Binance_API_key = environ['Binance_API_key']
Binance_Secret_key = environ['Binance_Secret_key']

exchange = ccxt.binance({
    'apiKey': Binance_API_key,
    'secret': Binance_Secret_key,
    'enableRateLimit': True,
    'options': {'defaultType': 'future',},})
######################

try:
    api.verify_credentials()
    print("Authentication OK")
except:
    print("Error during authentication")

######################################################################
######################################################################



######################################################################
#### Check continuellement si le dernier tweet d'Elon a été publié il y a moins de 3 sec.
#### Si c'est le cas, analyse s'il contient des termes liés au BTC/DOGE/ETH. 
#### Si pas de terme lié, rien ne se passe. Sinon, associe le tweet à une des 3 devises pour qu'un trade
#### soit passé par la suite
######################################################################

#### Montant investi et levier
InRiskAmount = 400
Levier = 40
######

### Configuration du levier
exchange.fapiPrivate_post_leverage({"symbol": "ETHUSDT", "leverage": Levier,})
exchange.fapiPrivate_post_leverage({"symbol": "DOGEUSDT", "leverage": Levier,})
exchange.fapiPrivate_post_leverage({"symbol": "BTCUSDT", "leverage": Levier,})

### 1st while, si un tweet d'intérêt a été trouvé et qu'un ordre a été placé, relance la boucle
while True:

### 2nd while, relance la boucle tant qu'un tweet datant de - de 3 sec n'a pas été trouvé    
    while True:
        print("Analysis",end="\r")
        time.sleep(0.25)
        starttime = time.time() 
    
### 3rd while, relance la recherche du dernier tweet en cas d'except (Tweepy instable, parfois ne trouve pas le tweet) 
        while True:
            try:
### Cherche le dernier tweet/status publié
                status = api.user_timeline("@elonmusk", count = 1)[0]
                TweetElon=status.text
            except:
### 'Continue' is triggered when there is an exception, and retries the while loop.
### If no exception, the 'break' breaks the 3rd while loop
                continue
            break #3   
        
### Transfo date en UTC psk le status.created_at de Tweepy les donne en UTC aussi
        today = datetime.datetime.now()
        UTC = datetime.timedelta(hours=-2)
        DateTimeUTC = today + UTC

        print("Ongoing ",end="\r")
        time.sleep(0.75)
### Break la 2nd while loop si le dernier tweet date de moins de 5 sec  
        if (DateTimeUTC - status.created_at).total_seconds() <= 5:
            break #2

### Si un tweet a été publié il y a moins de 5 sec, check le contenu du tweet et associe une devise de trading
### si le contenu du tweet y fait référence explicitement. 
### Sinon, ismeme = Yes, associe DOGE et book un ordre qui sera cancell si pas exécuté avant 15 sec. 
### But : exploiter un meme faisant ref au Doge ou pouvant faire bouger le marché sans avoir le mot doge ou btc etc qq part. 
### Si le tweet a rien a voir avec les crypto, les ordres seront tte façon cancell au bout de 20 sec 
### sans avoir été déclenchés (à priori)
    Currency = ""
    ismeme = "No"

    if TweetElon != "":
        myListDOGE = ['DOGE','Doge','doge','dog','Dog','DOG','DOGECOIN','Dogecoin','dogecoin']
        myListBTC = ['BTC','btc','Btc','Bitcoin','BITCOIN','bitcoin']
        myListETH = ['ETH','Eth','eth','ETHEREUM','Ethereum','ethereum','ETHER','Ether','ether']

        if any(x in TweetElon for x in myListDOGE):
            Currency = 'DOGE/USDT'
        elif any(y in TweetElon for y in myListBTC):  
            Currency = 'BTC/USDT'
        elif any(z in TweetElon for z in myListETH): 
            Currency = 'ETH/USDT'
        else:
            Currency = 'DOGE/USDT'
            ismeme = "Yes"
            
######################################################################    
#### Si une devise a été associée :
#### passe un ordre avec l'API de Binance en fonction de la currency d'intérêt du tweet   
######################################################################    

    
### Chope le spot de la devise du tweet
    CurrData = exchange.fetch_ticker(Currency)
    CryptoPrice = CurrData['last']

# exchange.verbose = True  # uncomment for debugging
### Global setup
    markets = exchange.load_markets()
    symbol = Currency
    sideDOWN = 'buy' 
    sideUP = 'sell'
    Size = InRiskAmount*Levier/CryptoPrice # = Montant en risque * levier / Prix spot
    price = None

### Trailing setup
    ActivationPriceUp = CryptoPrice*1.005 #1.005
    ActivationPriceDown = CryptoPrice*0.995 #0.995
    order_trailing = 'TRAILING_STOP_MARKET'
    rate = '0.5'
    paramsUP = {'activationPrice': ActivationPriceUp,'callbackRate': rate}
    paramsDOWN = {'activationPrice': ActivationPriceDown,'callbackRate': rate}

### Stop market setup
    order_stopmarket = 'STOP_MARKET'
    StopPriceUP = CryptoPrice*1.005 #1.003
    StopPriceDOWN = CryptoPrice*0.995 #0.997
    

#### Place sell Trailing order (déclenchement à la hausse)
    order = exchange.create_order(symbol, order_trailing, sideUP, Size, price, paramsUP,)

#### Place buy Trailing order (déclenchement à la baisse)
    order = exchange.create_order(symbol, order_trailing, sideDOWN, Size, price, paramsDOWN,)

#### Place sell Stop order (déclenchement à la baisse)
    order = exchange.create_order(symbol, order_stopmarket, sideUP, Size, price, {'stopPrice': StopPriceDOWN,},)

#### Place buy Stop order (déclenchement à la hausse)
    order = exchange.create_order(symbol, order_stopmarket, sideDOWN, Size, price, {'stopPrice': StopPriceUP,},)
    
    endtime = time.time()
    
    print("------- Mème ? ➜",ismeme,"-------")
    Balance0 = exchange.fetch_balance()['USDT']
    print("--- Balance :",Balance0,"---")
    print("--- Spot :",CryptoPrice,"---")
    print("--- Tweet ➜",TweetElon)
    print("--- Tweet posted at",status.created_at,"UTC ---")
    print("---",Currency,"orders placed at",(datetime.datetime.now().strftime("%H:%M:%S")),"CET ---")
    print("--- %s seconds to place orders ---" % (endtime - starttime),"\n")
    #print("--- Market parameters : Spot =",CryptoPrice,"- StopPriceUP =",StopPriceUP,"- StopPriceDOWN =",StopPriceDOWN,
     #    "- ActivationPriceUP =",ActivationPriceUp,"- ActivationPriceDOWN =",ActivationPriceDOWN,)
    
### Si le tweet ne fait textuellement référence à aucune devise, des ordres sont quand même bookés.
### Si aucun des quatre ordres n'a été déclenché au bout de 20 sec (ordres ouverts == 4), les ordres sont cloturés.
### Sinon, ordres cloturés au bout de 3 min.
    if ismeme == "Yes":
        time.sleep(20.0)
        if len(exchange.fetchOpenOrders(symbol)) == 4:
            close_order = exchange.cancel_all_orders(symbol)
            print("---",Currency,"orders closed at",(datetime.datetime.now().strftime("%H:%M:%S")),"---")
    
######################################################################    
#### Fermeture des ordres et positions au bout de 3 min
######################################################################    

    time.sleep(180.0)  

##### Close ordres non-exécutés        
    close_order = exchange.cancel_all_orders(symbol)
    
##### Close les positions (ordres exécutés)
### try/except/pass parce que si les ordres n'ont pas été exécutés, le close_position renvoie à une erreur vu que les
### positions n'existent pas

### Close sell Trailing position
    try:
        close_position = exchange.create_order(symbol, 'MARKET', sideDOWN, Size, price, params={"reduceOnly": True})
    except:
        pass
### Close buy Trailing position
    try:
        close_position = exchange.create_order(symbol, 'MARKET', sideUP, Size, price, params={"reduceOnly": True},)
    except:
        pass
### Close sell Stop position
    try:
        close_position = exchange.create_order(symbol, 'MARKET', sideDOWN, Size, price, params={"reduceOnly": True})
    except:
        pass
### Close buy Stop position
    try:
        close_position = exchange.create_order(symbol, 'MARKET', sideUP, Size, price, params={"reduceOnly": True})  
    except:
        pass
    
    print("---",Currency,"orders & positions closed at",(datetime.datetime.now().strftime("%H:%M:%S")),"---","\n")
    Balance1 = exchange.fetch_balance()['USDT']
    print("--- Balance :",Balance1,"---")
    print("--- PnL =",Balance1['total']-Balance0['total'],"---","\n")
    print("----------------------------------------------------------","\n")               

        #print(TweetElon)
        #print(Currency)    
        #time.sleep(3.0 - ((time.time() - starttime) % 3.0))
