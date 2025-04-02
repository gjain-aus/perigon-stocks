import json
import argparse
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime, date, timedelta
import logging

#local files
import prices
from prices import SecurityPrices


###################################################################################################
#define a simple stock Holding object - Ticker and Units
#units are float as for some securities you can hold partial shares
class Holding(dict):
    ticker: str
    units: float

    def __init__(self, ticker: str, units: float):
        self.ticker = ticker.upper()
        self.units = units
        dict.__init__(self,ticker=self.ticker,units=self.units) #make it easier to dump wiht JSON
    
    def __str__(self):
        return f"Holding(name={self.ticker}, unites={self.units})"

    def to_json_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def get_ticker(self) -> str:
        return self.ticker

    @classmethod
    def from_json_dict(cls, data: Dict[str, Any]) -> 'Holding':
        return cls(
            ticker=data["ticker"],
            units=data["ticker"]
        )

    
###################################################################################################
# create a list of holdings based on JSON file
def process_holdings(holdings_json: dict) -> list:
    holdings=list()
    for entry in holdings_json:
        new_entry = Holding(entry['ticker'],entry['units'])
        holdings.append(new_entry)

    return holdings


###################################################################################################
"""Load JSON data from a file and return it as a Python dictionary."""
def read_portfolio_from_file(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.critical(f"Error: File '{file_path}' not found")
        raise
    except json.JSONDecodeError as e:
        logging.critical(f"Error decoding JSON from file: {e}")
        raise
    except Exception as e:
        logging.critical(f"Unexpected error reading file: {e}")
        raise


###################################################################################################
def analyze_holdings(holdings, security_prices):
    for single_holding in holdings:
        ticker=single_holding.get_ticker()
        ticker_prices=security_prices.get_prices_for_ticker(ticker)
        num_prices=len(ticker_prices)
        overall_price_chg=(ticker_prices[-1][SecurityPrices.CLOSE]-ticker_prices[0][SecurityPrices.OPEN])
        overall_percent_chg = (overall_price_chg)/ticker_prices[0][SecurityPrices.OPEN]
        logging.info(f"{ticker} -- {num_prices} -- {overall_price_chg} -- {overall_percent_chg}")

###################################################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse JSON portfolio")
    parser.add_argument("-f","--filename", required=True, help="Path to the JSON file to parse")
    parser.add_argument("-d","--days", required=True, type=int, choices=range(1,32), help="Number of days to fetch data for (1 to 31)")

    logging.basicConfig(level=logging.INFO)
    
    # Parse arguments
    args = parser.parse_args()
    file_path = args.filename
    numdays = args.days

    portfolio_details = read_portfolio_from_file(file_path)
    holdings=process_holdings(portfolio_details['holdings'])
    logging.debug(json.dumps(holdings,indent=2))

    today = date.today()
    logging.debug(f"Today's date: {today}")

    startd = today - timedelta(days=numdays)
    logging.debug(f"Start date: {startd}")

    #Fetch prices for all the tickers in portfolio
    sp = prices.load_cached_prices()
    for single_holding in holdings:
        if sp.get_prices_for_ticker(single_holding.get_ticker())==None:
            sp.add_security(single_holding.get_ticker(), prices.fetch_prices(single_holding.get_ticker(), startd, today))
    
    logging.debug(json.dumps(sp,indent=2))

    with open(prices.PRICES_CACHE_FILE, 'w') as file:
        json.dump(sp, file, indent=2)
        logging.debug(f"wrote prices to {prices.PRICES_CACHE_FILE}")

    analyze_holdings(holdings, sp)