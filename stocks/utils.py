from stocks.models import Stock
# from analysis.models import Distribution
from transaction.models import Transaction
from portfolioitem.models import PortfolioItem
from portfolio.models import Portfolio
from stocks.models import Stock

# return - a string of tickers

def ticker_symbol_list():
    # return Stock.objects.filter(symbol="AMZY")
    return Stock.objects.all()


def update_portfolio(instance, price):
    try:
        portfolio_item = PortfolioItem.objects.filter(stock=instance)
        for item in portfolio_item:
            item.update_current_price(price)

    except PortfolioItem.DoesNotExist:
        print("Model does not exist.")

def update_stock(instance, price):
    instance.update_current_price(price)

def update_distribution(
        instance, dividend, ex_dividend_date, dividend_yield, pay_period, stock_name
    ):
    instance.update_information(dividend, ex_dividend_date, dividend_yield, pay_period, stock_name)

