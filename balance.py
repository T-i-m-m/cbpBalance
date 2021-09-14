#!/usr/bin/env python3
# encoding: utf-8

import json, sys
import pandas as pd
from models.exchange.coinbase_pro.api import AuthAPI as CBAuthAPI, PublicAPI as CBPublicAPI

def printHelp():
    print ('Create a config.json:')
    print ('* Add 1 or more portfolios', "\n")

    print ('{')
    print ('    "<portfolio_name>" : {')
    print ('        "api_key" : "<coinbase_pro_api_key>",')
    print ('        "api_secret" : "<coinbase_pro_api_secret>",')
    print ('        "api_pass" : "<coinbase_pro_api_passphrase>",')
    print ('    },')
    print ('    "<portfolio_name>" : {')
    print ('        "api_key" : "<coinbase_pro_api_key>",')
    print ('        "api_secret" : "<coinbase_pro_api_secret>",')
    print ('        "api_pass" : "<coinbase_pro_api_passphrase>",')
    print ('    }')
    print ('}', "\n")

    print ('<portfolio_name> - Coinbase Pro portfolio name E.g. "Default portfolio"')
    print ('<coinbase_pro_api_key> - Coinbase Pro API key for the portfolio')
    print ('<coinbase_pro_api_secret> - Coinbase Pro API secret for the portfolio')
    print ('<coinbase_pro_api_passphrase> - Coinbase Pro API passphrase for the portfolio')
    print ("\n")

try:
    if len(sys.argv) != 3 and sys.argv[1] != '--list':
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

            accounts = api.getAccounts()

            if sys.argv[1] == '--list':
                for index, row in accounts.iterrows():
                    print(row['currency'], '\t', round(float(row['balance']), 4))

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
    