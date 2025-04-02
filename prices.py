import os
import requests
import json
from polygon import RESTClient
from datetime import datetime, date, timedelta
import argparse
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import logging

from dotenv import load_dotenv
load_dotenv()

PRICES_CACHE_FILE="prices.cache"

###################################################################################################
#define dictionary of prices for tickers
class SecurityPrices(dict):
    #constants
    OPEN="open"
    CLOSE="close"
    DATE="date"
    PRICE_CHG="price_chg"
    PERCENT_CHG="percent_chg"

    def __init__(self):
        dict.__init__(self)

    def __init__(self, data):
        dict.__init__(self, data)
    
    def add_security(self, ticker: str, prices: list):
        self[ticker.upper()]=prices

    def get_prices_for_ticker(self, ticker):
        ticker_uc=ticker.upper()
        return (None if ticker_uc not in self else self[ticker_uc])

    @classmethod
    def from_json_dict(cls, data: Dict[str, Any]) -> 'SecurityPrices':
        sp = SecurityPrices(data)
        return sp
            
###################################################################################################
#fetch prices from polygon.io for a given security and date range
#return a list of open, close, date, and percent change/amount dicts
def fetch_prices(ticker: str, startd: str, endd: str) -> list:
    client = RESTClient(os.getenv('POLYGON_API_KEY'))
    logging.info(f"Fetching prices from polygon.ai for {ticker}")
    aggs = []
    for a in client.list_aggs(ticker.upper(),1,"day",startd,endd,adjusted="true",sort="asc",limit=120):
        aggs.append(a)

    prices = list()
    for agg in aggs:
        prev_close = agg.open if not prices else prices[-1]['close']
        new_entry= {
            SecurityPrices.OPEN: agg.open,
            SecurityPrices.CLOSE: agg.close,
            SecurityPrices.DATE: datetime.fromtimestamp(agg.timestamp/1000).strftime("%Y%m%d"),
            SecurityPrices.PRICE_CHG: agg.close-prev_close,
            SecurityPrices.PERCENT_CHG: (agg.close-prev_close)/prev_close
        }
        prices.append(new_entry)

    return prices

###################################################################################################
def load_cached_prices():
    filepath=PRICES_CACHE_FILE
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return SecurityPrices.from_json_dict(data)
        except json.JSONDecodeError:
            logging.warning(f"Error: File '{filepath}' is not valid JSON.")
            return SecurityPrices({})
    else:
        logging.info(f"Error: File '{filepath}' does not exist.")
        return SecurityPrices({})

###################################################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse JSON portfolio")
    parser.add_argument("-t","--ticker", required=True, help="Ticker to fetch data for")
    parser.add_argument("-d","--days", required=True, type=int, choices=range(1,32), help="Number of days to fetch data for (1 to 31)")
    
    # Parse arguments
    args = parser.parse_args()
    ticker = args.ticker.upper()
    numdays = args.days

    today = date.today()
    logging.debug(f"Today's date: {today}")

    startd = today - timedelta(days=numdays)
    logging.debug(f"Start date: {startd}")

    sp = load_cached_prices()
    sp.add_security(ticker, fetch_prices(ticker, startd, today))

    logging.debug(json.dumps(sp,indent=2))

    with open(PRICES_CACHE_FILE, 'w') as file:
        json.dump(sp, file, indent=2)
