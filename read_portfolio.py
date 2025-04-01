import json
import argparse
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict


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


    @classmethod
    def from_json_dict(cls, data: Dict[str, Any]) -> 'Holding':
        return cls(
            ticker=data["ticker"],
            units=data["ticker"]
        )

###################################################################################################
#define dictionary of prices for a given ticker
class SecurityPrices(dict):
    def __init__(self):
        dict.__init__(self)
    
    def add_security(self, ticker: str, prices: dict):
        sorted_price_dates = sorted(prices.items())
        sorted_prices_dict = dict(sorted_price_dates)
        
        ticker_lc = ticker.lower()
        self[ticker_lc.lower()]=dict()
        self[ticker_lc.lower()]["dates"]=list(sorted_prices_dict.keys())
        self[ticker_lc.lower()]["values"]=list(sorted_prices_dict.values())
    
###################################################################################################
# create a list of holdings based on JSON file
def process_holdings(holdings_json: dict) -> list:
    holdings=list()
    for entry in holdings_json:
        new_entry = Holding(entry['ticker'],entry['units'])
        holdings.append(new_entry)

    return holdings

# create a list of holdings based on JSON file
def process_prices(prices_json: dict) -> list:
    sec_prices = SecurityPrices()
    for ticker in prices_json:
        sec_prices.add_security(ticker, prices_json[ticker])

    return sec_prices


###################################################################################################
"""Load JSON data from a file and return it as a Python dictionary."""
def read_portfolio_from_file(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        raise
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from file: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error reading file: {e}")
        raise


###################################################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse JSON portfolio")
    parser.add_argument("-f","--filename", required=True, help="Path to the JSON file to parse")
    
    # Parse arguments
    args = parser.parse_args()
    file_path = args.filename

    portfolio_details = read_portfolio_from_file(file_path)
    print(json.dumps(portfolio_details,indent=2))

    holdings=process_holdings(portfolio_details['holdings'])
    print(json.dumps(holdings,indent=2))

    sec_prices=process_prices(portfolio_details['close_prices'])
    print(json.dumps(sec_prices,indent=2))
