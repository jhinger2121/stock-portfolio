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

    def stock_data(self):
        if not self.symbol_data:
            self.symbol_data = yf.Ticker(self.symbol, session=self.session)
        return self

    def get_ticker_information(self):
        if self.symbol_data:
            self.stock_information = self.symbol_data.info
            print(self.stock_information)
        return self
    
    def get_stock_name(self):
        info = self.symbol_data.info
        if "longName" in info:
            return self.symbol_data.info['longName']
        elif "shortName" in info:
            return self.symbol_data.info['shortName']
        else:
            return ""
    
    def get_history(self, time="1mo"):
        hist = self.symbol_data.history(time)
        print(hist)
        return None
    
    def get_dividends_info(self):
        actions = self.symbol_data.dividends
        if actions.count() == 0:
            return None
        date_format = "%Y-%m-%d %H:%M:%S%z"

        date_1 = str(actions.tail(2).index[0])
        date_2 = str(actions.tail(2).index[1])
        datetime_object_1 = datetime.strptime(date_1, date_format)
        datetime_object_2 = datetime.strptime(date_2, date_format)
        defference = datetime_object_2 - datetime_object_1

        pay_period = ""
        if int(defference.days) < 40:
            pay_period = "monthly"
        elif int(defference.days) > 40:
            pay_period = "quarterly"
        last_row =  actions.tail(1)
        # ex-dividend-date last_row.index[0]
        return {"ex_dividend_date": datetime_object_2, 
                "dividend": last_row.iloc[0], "pay_period": pay_period}
    
    def get_price(self):
        info = self.symbol_data.info
        if 'currentPrice' in info:
            print("current")
            return info['currentPrice']
        elif 'previousClose' in info:
            print("previous")
            return info['previousClose']
        else:
            logging.info('Market price can not be found in data.')
            return None

    def get_stock_yeild(self, price, pay_period, dividend):
        if price and dividend and pay_period:
            s_yield = self.get_stock_dYield()
            if s_yield:
                return s_yield
            annual_dividend = 0
            if pay_period == "monthly":
                annual_dividend = dividend * 12
            elif pay_period == "quarterly":
                annual_dividend = dividend * 4
            
            stock_yield = (annual_dividend * price) / 100
            return stock_yield
        else:
            return 0
    
    def get_all_stock_info(self):
        return self.symbol_data
    
    #last ex-dividend date
    def exDividendDate(self):
        value = self.is_value_exist('exDividendDate')
        if value:
            # now conver to data
            pass
        # print(pd.to_datetime(int(self.symbol_data['exDividendDate']), 
        #                format="%m/%d/%Y"))
        # if 'exDividendDate' in self.symbol_data:
        #     return self.symbol_data['exDividendDate']
        # datetime = int(self.symbol_data['exDividendDate'])
        return datetime.now()
    
    def lastDividendValue(self):
        return self.is_value_exist('lastDividendValue')
    
    def get_stock_dYield(self):
        return self.is_value_exist('dividendYield')

    # Check if "key" is in dict, if not return log error, or data
    def is_value_exist(self, strr):
        if strr in self.symbol_data.info:
            return self.symbol_data.info[strr]
        else:
            return None


