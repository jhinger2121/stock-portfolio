import yfinance as yf
import pandas as pd
from datetime import datetime, timezone, timedelta
import logging

from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter

class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass

session = CachedLimiterSession(
    limiter=Limiter(RequestRate(2, Duration.SECOND*10)),  # max 2 requests per 5 seconds
    bucket_class=MemoryQueueBucket,
    backend=SQLiteCache("yfinance.cache"),
)


class Symbol:
    def __init__(self, symbol):
        self.session = session
        self.symbol = symbol
        self.symbol_data = None
        self.stock_information = None

    def fetch_symbol_data(self):
        if not self.symbol_data:
            logging.info("Fetching data from server for symbol: %s", self.symbol)
            self.symbol_data = yf.Ticker(self.symbol, session=self.session)
        return self.symbol_data

    def get_ticker_information(self):
        if not self.stock_information:
            self.fetch_symbol_data()
            self.stock_information = self.symbol_data.info
            logging.info("Stock information: %s", self.stock_information)
        return self.stock_information
    
    def get_stock_name(self):
        info = self.get_ticker_information()
        return info.get('longName') or info.get('shortName', '')
    
    def stock_summary(self):
        info = self.get_ticker_information()
        return info.get('longBusinessSummary', '')
    
    def get_history(self, period="1mo"):
        symbol_data = self.fetch_symbol_data()
        hist = symbol_data.history(period=period)
        logging.info("Historical data for %s: %s", self.symbol, hist)
        return hist
    
    def get_dividends_info(self):
        self.fetch_symbol_data()
        actions = self.symbol_data.dividends
        if actions.empty:
            return None
        
        last_two_dividends = actions.tail(2)
        if len(last_two_dividends) < 2:
            return None

        date_format = "%Y-%m-%d %H:%M:%S%z"
        datetime_object_1 = datetime.strptime(str(last_two_dividends.index[0]), date_format)
        datetime_object_2 = datetime.strptime(str(last_two_dividends.index[1]), date_format)
        difference = datetime_object_2 - datetime_object_1

        pay_period = ""
        if difference.days < 10:
            pay_period = "weekly"
        elif difference.days < 37:
            pay_period = "monthly"
        else:
            pay_period = "quarterly"
         
        last_dividend = last_two_dividends.iloc[1]
        return {
            "ex_dividend_date": datetime_object_2, 
            "dividend": last_dividend, 
            "pay_period": pay_period
        }
    
    def get_price(self):
        info = self.get_ticker_information()
        return info.get('currentPrice') or info.get('previousClose')

    def get_stock_yield(self, price, pay_period, dividend):
        if not (price and dividend and pay_period):
            return 0
        
        s_yield = self.get_stock_dividend_yield()
        if s_yield:
            return s_yield

        annual_dividend = dividend * (12 if pay_period == "monthly" else 4)
        return round((annual_dividend / price) * 100, 2)
    
    def get_all_stock_info(self):
        return self.symbol_data
    
    #last ex-dividend date
    def get_ex_dividend_date(self):
        ex_div_date = self._get_info_value('exDividendDate')
        if ex_div_date:
            return pd.to_datetime(ex_div_date, format="%Y-%m-%d")
        return None
    
    def _get_info_value(self, key):
        info = self.get_ticker_information()
        return info.get(key)
    
    def lastDividendValue(self):
        return self.is_value_exist('lastDividendValue')
    
    def get_stock_dividend_yield(self):
        info = self.get_ticker_information()
        return info.get('dividendYield')


