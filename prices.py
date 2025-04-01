import os
import requests
import json
from polygon import RESTClient
from datetime import datetime, date, timedelta
import argparse

from dotenv import load_dotenv
load_dotenv()

###################################################################################################
#define dictionary of prices for tickers
class SecurityPrices(dict):
    def __init__(self):
        dict.__init__(self)
    
    def add_security(self, ticker: str, prices: list):
        self[ticker.upper()]=prices

    def get_prices_for_security(self, ticker):
        ticker_uc=ticker.upper()
        return (None if ticker_uc not in self else self[ticker_uc])
            
###################################################################################################
#fetch prices from polygon.io for a given security and date range
#return a list of open, close, date, and percent change/amount dicts
def fetch_prices(ticker: str, startd: str, endd: str) -> list:
    client = RESTClient(os.getenv('POLYGON_API_KEY'))

    aggs = []
    for a in client.list_aggs(ticker,1,"day",startd,endd,adjusted="true",sort="asc",limit=120):
        aggs.append(a)

    prices = list()
    for agg in aggs:
        prev_close = agg.open if not prices else prices[-1]['close']
        new_entry= {
            'open':agg.open,
            'close':agg.close,
            'date':datetime.fromtimestamp(agg.timestamp/1000).strftime("%Y%m%d"),
            'price_chg': agg.close-prev_close,
            'percent_chg': (agg.close-prev_close)/prev_close
        }
        prices.append(new_entry)

    return prices


###################################################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse JSON portfolio")
    parser.add_argument("-t","--ticker", required=True, help="Ticker to fetch data for")
    parser.add_argument("-d","--days", required=True, type=int, choices=range(1,32), help="Number of days to fetch data for (1 to 31)")
    
    # Parse arguments
    args = parser.parse_args()
    ticker = args.ticker.upper()
    numdays = args.days

    print(ticker)
    print(numdays)

    today = date.today()
    print("Today's date:", today)

    startd = today - timedelta(days=numdays)
    print("Start date:", startd)

    sp = SecurityPrices()
    sp.add_security(ticker, fetch_prices(ticker, startd, today))
    sp.add_security('FDS', fetch_prices('FDS',startd, today))

    print(json.dumps(sp,indent=2))

    print(json.dumps(sp.get_prices_for_security('fds'),indent=2))
    print(json.dumps(sp.get_prices_for_security('googl'),indent=2))