#!/usr/bin/env python3
# encoding: utf-8

import json, sys
import pandas as pd
from datetime import date
from datetime import datetime

from models.exchange.coinbase_pro.api import AuthAPI as CBAuthAPI, PublicAPI as CBPublicAPI

def printHelp():
    print ('Create a config.json:')
    print ('* Add 1 or more portfolios', "\n")

    print ('{')
    print ('    "Portfolio" : {')
    print ('        "name" : "<portfolio_name>",')
    print ('        "api_key" : "<coinbase_pro_api_key>",')
    print ('        "api_secret" : "<coinbase_pro_api_secret>",')
    print ('        "api_pass" : "<coinbase_pro_api_passphrase>",')
    print ('        "log_file" : "<log_file>",')
    print ('        "market_file" : "<market_list>",')
    print ('    },')
    print ('    "Portfolio" : {')
    print ('        "name" : "<portfolio_name>",')
    print ('        "api_key" : "<coinbase_pro_api_key>",')
    print ('        "api_secret" : "<coinbase_pro_api_secret>",')
    print ('        "api_pass" : "<coinbase_pro_api_passphrase>",')
    print ('        "log_file" : "<log_file>",')
    print ('        "market_file" : "<market_list>",')
    print ('    }')
    print ('}', "\n")

    print ('<portfolio_name> - Coinbase Pro portfolio name E.g. "Default portfolio"')
    print ('<coinbase_pro_api_key> - Coinbase Pro API key for the portfolio')
    print ('<coinbase_pro_api_secret> - Coinbase Pro API secret for the portfolio')
    print ('<coinbase_pro_api_passphrase> - Coinbase Pro API passphrase for the portfolio')
    print ('<log_file> - Path and name of log file')
    print ('<market_list> - Path and name of market list file')
    print ("\n")

try:
    if len(sys.argv) != 3 and sys.argv[1] != '--list' and sys.argv[1] != '--log':
        raise Exception(f"Arguments missing. E.g. base and quote currency (e.g. DOT EUR)")

    with open('config.json') as config_file:
        json_config = json.load(config_file)
    if not isinstance(json_config, dict):
        raise TypeError('config.json is invalid.')

    if len(list(json_config)) < 1:
        printHelp()
        sys.exit()

    df_tracker = pd.DataFrame()

    for portfolio in list(json_config):
        base_currency = ''
        quote_currency = ''
        market = ''

        portfolio_config = json_config[portfolio]

        if ('api_key' in portfolio_config and 'api_secret' in portfolio_config and 'api_pass' in portfolio_config):
            api_key = portfolio_config['api_key']
            api_secret = portfolio_config['api_secret']
            api_pass = portfolio_config['api_pass']
            api = CBAuthAPI(api_key, api_secret, api_pass)

            log_filename = portfolio_config['log_file']
            market_filename = portfolio_config['market_file']

            accounts = api.getAccounts()

            if sys.argv[1] == '--list':
                total_balance = 0

                for index, row in accounts.iterrows():
                    if (row['currency'] != 'EUR'):
                        ticker = api.getTicker(row['currency'] + "-EUR")
                        print(
                            row['currency'], '\t',
                            round(float(row['balance']), 2), '\t', 
                            round(float(ticker.loc[0, 'price']), 2), '\t', 
                            round(float(row['balance']) * float(ticker.loc[0, 'price']), 2)
                        )
                        total_balance += float(row['balance']) * float(ticker.loc[0, 'price'])    
                print('\nEur\t', round(total_balance, 2), '\n')
                
            elif sys.argv[1] == '--log':
                total_balance = 0

                df = None        
                df = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M"), total_balance]], columns=['date', 'time', 'total balance (EUR)'])    

                with open(market_filename,'r') as market_file:
                    markets = market_file.read().splitlines()
                markets = filter(None, markets)

                # iterate throug all markets defined in Rey-market.list
                for market in markets:                    
                    ticker = api.getTicker(market + "-EUR") 
                    found = None
                    
                    #iterate through all currencies in coinbase portfolio
                    for index, row in accounts.iterrows():
                        if row['currency'] == market:
                            found = index
                    
                    if found != None:
                        df[market + ' balance'] =  float(accounts.loc[found, 'balance'])
                        df[market + ' rate'] =  ticker.loc[0, 'price']
                        df[market + ' value (EUR)'] =  float(accounts.loc[found, 'balance']) * float(ticker.loc[0, 'price'])
                        total_balance += float(accounts.loc[found, 'balance']) * float(ticker.loc[0, 'price'])

                    else:
                        df[market + ' balance'] =  0.0
                        df[market + ' rate'] =  ticker.loc[0, 'price']
                        df[market + ' value (EUR)'] =  0.0
                                
                df.loc[0, 'total balance (EUR)'] = round(total_balance, 2)
        
                # create file if it does not exist yet!
                log_file = Path(log_filename)
                if log_file.is_file():
                    df.to_csv(log_file, mode='a', header=False)
                else:
                    df.to_csv(log_filename)

            else:
                balanceBase = 0
                balanceQuote = 0
                for index, row in accounts.iterrows():
                    if row['currency'] == sys.argv[1]:
                        balanceBase = float(row['balance'])
                    if row['currency'] == sys.argv[2]:
                        balanceQuote = float(row['balance'])
                        
                market = sys.argv[1] + "-" + sys.argv[2]
                product = api.getProduct(market)
                minBase = float(product['base_min_size'])
                minQuote = float(product['min_market_funds'])

                if balanceBase > minBase or balanceQuote > minQuote:
                    sys.exit(0)
                else:
                    if balanceBase <= minBase:
                        print('Not enough ', sys.argv[1])
                    if balanceQuote <= minQuote:
                        print('Not enough ', sys.argv[2])
                    sys.exit(1)

        else:
            printHelp()
            sys.exit()

            #break

except IOError as err:
    print("IO Error:")
    print (err)
except Exception as err:
    print("Exception:")
    print (err)
    
