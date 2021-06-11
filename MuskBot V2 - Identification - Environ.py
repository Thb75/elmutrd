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