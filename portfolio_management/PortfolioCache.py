import time, decimal, json
from collections import defaultdict
from abc import ABC, abstractmethod

from django.conf import settings
from django.core.cache import cache
from django.core import serializers

from transaction.models import Transaction
from transaction.tasks import update_defiance_stocks, update_portfolio_items
from portfolio.models import Portfolio


class AdjustmentStrategy(ABC):
    @abstractmethod
    def adjust(self, portfolio, stock_symbol):
        pass
class TSLYAdjustmentStrategy(AdjustmentStrategy):
    def adjust(self, portfolio, stock_symbol):
        val = portfolio['holdings'][stock_symbol]['quantity'] / 2
        portfolio['holdings'][stock_symbol]['quantity'] = round(val, 4)

        price = portfolio['holdings'][stock_symbol]['avg_price'] * 2
        portfolio['holdings'][stock_symbol]['avg_price'] = round(price, 4)

class Defiance_1_for_3(AdjustmentStrategy):
    def adjust(self, portfolio, stock_symbol):
        val = portfolio['holdings'][stock_symbol]['quantity'] / 3
        portfolio['holdings'][stock_symbol]['quantity'] = round(val, 4)

        price = portfolio['holdings'][stock_symbol]['avg_price'] * 3
        portfolio['holdings'][stock_symbol]['avg_price'] = round(price, 4)

class PortfolioAdjuster:
    def __init__(self, strategy: AdjustmentStrategy):
        self._strategy = strategy
    
    def set_strategy(self, strategy: AdjustmentStrategy):
        self._strategy = strategy
    
    def execute(self, portfolio, stock_symbol):
        self._strategy.adjust(portfolio, stock_symbol)

def update_defiance_stocks(portfolio):
    adjustments = [
        {"symbol": "QQQY", "strategy": Defiance_1_for_3()},

        {"symbol": "IWMY", "strategy": Defiance_1_for_3()},
    ]

    for adj in adjustments:
        if not adj['symbol'] in portfolio['holdings']:
            continue
        adjuster = PortfolioAdjuster(adj["strategy"])
        adjuster.execute(portfolio, adj['symbol'])

def update_portfolio_items(portfolio):
    adjustments = [
        {"symbol": "TSLY", "strategy": TSLYAdjustmentStrategy()},
    ]

    for adj in adjustments:
        if not adj['symbol'] in portfolio['holdings']:
            continue
        adjuster = PortfolioAdjuster(adj["strategy"])
        adjuster.execute(portfolio, adj['symbol'])

class PortfolioCache:
    _cache = defaultdict(dict)
    _cache_expiry = defaultdict(dict)
    CACHE_TIMEOUT = 3600

    def __init__(self, user):
        self.user = user

    def setup_cache(self):
        """
        Initialize the cache structure for the user and portfolio if it doesn't exist.
        """
        self._cache['dividends'] = {
            'dividends_by_stocks': {},
            'time_period': {},
        }

    def _initialize_cache(self):
        transactions = Transaction.objects.filter(user=self.user)

        for transaction in transactions:
            if not transaction.portfolio.id in self._cache:
                self._cache[transaction.portfolio.id] = {}
            self._update_cache(transaction)

        return self._cache


    def _update_cache(self, transaction):
        # Update individual stock holdings, dividends, etc.
        # if self.portfolio.id not in self._cache[self.user.id]:
        #     self._cache[self.user.id][self.portfolio.id] = {
        #         'total_holding_amount': 0,
        #         'holdings': {},
        #         'dividends': {},
        #     }

        if not 'holdings' in self._cache[transaction.portfolio.id]:
            self._cache[transaction.portfolio.id]['holdings'] = {}
        holdings = self._cache[transaction.portfolio.id]['holdings']
        stock_symbol = transaction.stock.symbol

        

        # **** HOLDINGS ****
        if stock_symbol not in holdings:
            holdings[stock_symbol] = {
                'avg_price': transaction.price,
                'quantity': transaction.quantity
            }
        else:
            # Calculate new quantity and average price based on the transaction type
            if transaction.transaction_type == 'BY':
                # Update quantity
                prev_quantity = holdings[stock_symbol]['quantity']
                prev_avg_price = holdings[stock_symbol]['avg_price']

                prev_total = prev_avg_price * decimal.Decimal(prev_quantity)
                current_total = transaction.price * decimal.Decimal(transaction.quantity)
                total_share = transaction.quantity + prev_quantity
                
                avg_cost_per_share = (prev_total + current_total) / decimal.Decimal(total_share)

                holdings[stock_symbol]['avg_price'] = avg_cost_per_share
                holdings[stock_symbol]['quantity'] = total_share
            
            elif transaction.transaction_type == 'SL':
                holdings[stock_symbol]['quantity'] -= transaction.quantity
                if holdings[stock_symbol]['quantity'] < 0.009:
                    del holdings[stock_symbol]

        if transaction.email_id == "18e2dec0afed1a00":
            for portfolio_items in self._cache.values():
                update_portfolio_items(portfolio_items)
        elif transaction.email_id == '19116cbbd5b69469':
            for portfolio_items in self._cache.values():
                update_defiance_stocks(portfolio_items)


        # **** DIVIDENDS ****

        # if its not dividend earning then don't go through here(into dividend calculations)
        if transaction.transaction_type != 'DR':
            return

        if not 'dividends' in self._cache[transaction.portfolio.id]:
            self._cache[transaction.portfolio.id]['dividends'] = {
                    'dividends_by_stocks': {},
                    'time_period': {},
                }
        dividends = self._cache[transaction.portfolio.id]['dividends']

        total_price = transaction.price
        if transaction.stock.currency == "USD":
            total_price *= decimal.Decimal(settings.CAD_TO_USD)
        total_price = round(total_price, 2)

        # Update total dividend received
        if not 'portfolio_total_dividends' in dividends:
            dividends['portfolio_total_dividends'] = total_price
        else:
            dividends['portfolio_total_dividends'] += total_price

        # Extract date components
        month = str(transaction.transaction_date.strftime("%B"))
        day = str(transaction.transaction_date.day)
        year = str(transaction.transaction_date.year)
        # date = f"{month} {day}"  key for monthly line chart

        # Update annual-based dividend data
        if year not in dividends['time_period']:
            dividends['time_period'][year] = {"total": 0}
        if month not in dividends['time_period'][year]:
            dividends['time_period'][year][month] = {"total": 0, "stocks": []}
        
        dividends['time_period'][year]["total"] += total_price
        dividends['time_period'][year][month]["total"] += total_price

        dividends['time_period'][year][month]["stocks"].append({
            "symbol": stock_symbol,
            "amount": total_price,
            "date": transaction.transaction_date
        })

        # dividend by stocks
        if stock_symbol in dividends['dividends_by_stocks']:
            dividends['dividends_by_stocks'][stock_symbol] += total_price
        else:
            dividends['dividends_by_stocks'][stock_symbol] = total_price




    def _cache_key(self, user_id=None):
        """Helper function to generate a unique cache key"""
        if user_id is None:
            user_id = self.user.id
        return f'portfolio_cache_{user_id}'

    def get_cache(self, user_id=None):
        cache_key = self._cache_key(user_id)
        cached_data = cache.get(cache_key)
        if cached_data is None:
            print("Cache miss, refreshing cache...")
            self.refresh_cache(user_id)
            cached_data = cache.get(cache_key)
        else:
            print("Cache hit, data found!")
        return cached_data

    def refresh_cache(self, user_id=None):
        cache_key = self._cache_key(user_id)
        cache_data = self._initialize_cache()  # Generate fresh cache data
        cache.set(cache_key, cache_data, timeout=self.CACHE_TIMEOUT)
        print(f"Cache refreshed for {cache_key}")

    def clear_cache(self):
        cache.clear()
