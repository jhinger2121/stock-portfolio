import logging
from celery import shared_task

from stocks.utils import ticker_symbol_list, update_distribution, update_portfolio, update_stock
from stocks.scrape_stock_info import Symbol
from stocks.models import Stock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockInformation:
    def __init__(self):
        stock_data = None
    

    def get_symbol_data(self, stock_obj):
        """Fetch data for a single stock symbol."""
        try:
            symbol = Symbol(stock_obj.yahoo_ticker_symbol)

            stock_name = symbol.get_stock_name()

            dividend_info = symbol.get_dividends_info()

            price = symbol.get_price()
            dividend = dividend_info["dividend"]
            pay_period = dividend_info["pay_period"]
            stock_yield = symbol.get_stock_yield(price, pay_period, dividend)

            return {
                "name": stock_name,
                "price": price,
                "ex_date": dividend_info["ex_dividend_date"],
                "dividend": dividend,
                "pay_period": pay_period,
                "yield": stock_yield
            }

        except Exception as e:
            logger.error(f"Error fetching data for symbol {stock_obj.yahoo_ticker_symbol}: {e}")
            return None

    def extract_data(self):
        symbols = ticker_symbol_list()
        data = {}

        for stock_obj in symbols:
            logger.info(f"Processing {stock_obj.symbol} ({stock_obj.yahoo_ticker_symbol})")
            stock_data = self.get_symbol_data(stock_obj)
            if stock_data:
                data[stock_obj] = stock_data
                logger.info(f"Stock Name: {stock_data['name']}, Price: {stock_data['price']}, "
                            f"Yield: {stock_data['yield']}, Ex-Date: {stock_data['ex_date']}, "
                            f"Pay Period: {stock_data['pay_period']}, Dividend: {stock_data['dividend']}")

        return data
    
    def update_stock_info(self):
        logger.info("Updating stock information...")
        self.stock_data = self.extract_data()
        if self.stock_data:
            logger.info("Stock information updated successfully.")
        else:
            logger.warning("No stock information found.")

    def reset_data(self):
        logger.info("Resetting stock data...")
        self.stock_data = None
        logger.info("Stock data reset successfully.")

    def update_price(self):
        if self.stock_data:
            logger.info("Updating stock prices...")
            for stock_obj, details in self.stock_data.items():
                # Update stock price
                update_stock(stock_obj, details['price'])
                # Update portfolio item price
                update_portfolio(stock_obj, details['price'])
            logger.info("Stock prices updated successfully.")
        else:
            logger.warning("No data found to update prices.")

    def update_distribution(self):
        if self.stock_data:
            logger.info("Updating stock distribution...")
            for stock_obj, details in self.stock_data.items():
                update_distribution(
                    stock_obj, details['dividend'], details['ex_date'],
                    details['yield'], details['pay_period'], details['name']
                )
            logger.info("Stock distribution updated successfully.")
        else:
            logger.warning("No data found to update distribution.")


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