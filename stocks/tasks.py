from celery import shared_task

from stocks.utils import ticker_symbol_list, update_distribution, update_portfolio, update_stock
from stocks.scrape_stock_info import Symbol
from stocks.models import Stock


class StockInformation:
    def __init__(self):
        stock_data = None

    def extrat_data(self):
        # get ticker sumbols
        symbols = ticker_symbol_list()
        data = {}
        for stock_obj in symbols:
            print(stock_obj.symbol, stock_obj.yahoo_ticker_symbol)
            symbol = Symbol(stock_obj.yahoo_ticker_symbol)

            stock_name = symbol.stock_data().get_stock_name()
            if stock_name:
                #ret:dct ex_dividend_date, dividend
                dividend_info = symbol.stock_data().get_dividends_info()
                if dividend_info:
                    price = symbol.stock_data().get_price()
                    ex_dividend_date = dividend_info["ex_dividend_date"]
                    dividend = dividend_info["dividend"]
                    pay_period = dividend_info["pay_period"]

                    s_yield = symbol.stock_data().get_stock_yeild(price, pay_period, dividend)
                    data[stock_obj] = {
                        "name": stock_name, "price": price, "ex_date": ex_dividend_date,
                        "dividend": dividend, "pay_period": pay_period, "yield": s_yield
                    }
                    print("Stock Name:", stock_name, "price:", price, "yield:", s_yield, 
                    "ex_date:", ex_dividend_date, "pay_period:", pay_period, "dividend:", dividend)
        return data
    
    def update_stock_info(self):
        self.stock_data = self.extrat_data()

    def reset_data(self):
        self.stock_data = None

    def update_price(self):
        stock_data = self.stock_data
        if stock_data:
            for value in stock_data:
                # update stock price
                update_stock(value, stock_data[value]['price'])
                # update portfolio_item price
                update_portfolio(value, stock_data[value]['price'])
        else:
            print("No data found")

    def update_distribution(self):
        if self.stock_data:
            for value in self.stock_data:
                stock_name = self.stock_data[value]["name"]
                s_yield = self.stock_data[value]["yield"]
                ex_dividend_date = self.stock_data[value]["ex_date"]
                pay_period = self.stock_data[value]["pay_period"]
                dividend = self.stock_data[value]["dividend"]

                update_distribution(value, dividend, ex_dividend_date, s_yield, pay_period, stock_name)

        else:
            print("No data found")


stock = StockInformation()
def get_data():
    stock.update_stock_info()

def reset_data():
    stock.reset_data()
    print(stock.stock_data)

def update_price():
    stock.update_price()

def update_stock_information():
    stock.update_distribution()