from celery import shared_task
from transaction.scrape_emails import GmailAnalyzerSingleton, EmailParser
from transaction.models import Transaction
from portfolioitem.models import PortfolioItem
from portfolio.models import Portfolio
from stocks.models import Stock
import decimal
from django.contrib.auth.models import User
from abc import ABC, abstractmethod

GmailAnalyzer = GmailAnalyzerSingleton()
EmailParser = EmailParser()

class AdjustmentStrategy(ABC):
    @abstractmethod
    def adjust(self, item):
        pass
class TSLYAdjustmentStrategy(AdjustmentStrategy):
    def adjust(self, item):
        val = item.quantity / 2
        price = item.purchase_price * 2
        item.quantity = round(val, 4)
        item.purchase_price = round(price, 4)
        item.save()

class Defiance_1_for_3(AdjustmentStrategy):
    def adjust(self, item):
        val = item.quantity / 3
        price = item.purchase_price * 3
        item.quantity = round(val, 4)
        item.purchase_price = round(price, 4)
        item.save()

class PortfolioAdjuster:
    def __init__(self, strategy: AdjustmentStrategy):
        self._strategy = strategy
    
    def set_strategy(self, strategy: AdjustmentStrategy):
        self._strategy = strategy
    
    def execute(self, item):
        self._strategy.adjust(item)

def update_defiance_stocks():
    adjustments = [

        {"symbol": "QQQY", "account_type": "tax_free", "strategy": Defiance_1_for_3()},
        {"symbol": "QQQY", "account_type": "FHSA", "strategy": Defiance_1_for_3()},
        {"symbol": "QQQY", "account_type": "RRSP", "strategy": Defiance_1_for_3()},

        {"symbol": "IWMY", "account_type": "tax_free", "strategy": Defiance_1_for_3()},
    ]

    for adj in adjustments:
        item = PortfolioItem.objects.get(stock__symbol=adj["symbol"], portfolio__account_type=adj["account_type"])
        adjuster = PortfolioAdjuster(adj["strategy"])
        adjuster.execute(item)

def update_portfolio_items():
    adjustments = [
        {"symbol": "TSLY", "account_type": "tax_free", "strategy": TSLYAdjustmentStrategy()},
        {"symbol": "TSLY", "account_type": "FHSA", "strategy": TSLYAdjustmentStrategy()},
    ]

    for adj in adjustments:
        item = PortfolioItem.objects.get(stock__symbol=adj["symbol"], portfolio__account_type=adj["account_type"])
        adjuster = PortfolioAdjuster(adj["strategy"])
        adjuster.execute(item)


@shared_task
def process_gmail_emails():
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    gmail_analyzer = GmailAnalyzer.get_instance(SCOPES)
    messages = gmail_analyzer.fetch_emails()
    for msg in messages:
        email_data = gmail_analyzer.get_email_data(gmail_analyzer.service, msg)
        if email_data:
            email_info = EmailParser.process_email(email_data)
            if email_info:
                stop_flag = save_to_database(email_info)

def save_to_database(emails):

    email_id = emails['id'].strip()
    account = emails['account'].strip()
    shares = emails['shares'].strip()
    avg_price = emails['avg_price'].strip()
    total_cost = emails['total_cost'].strip()
    symbol = emails['symbol'].strip()
    type_ = emails['type'].strip()
    time = emails['date']

    if not shares and not total_cost:
        shares = total_cost = 0.0
    account_types = {
        "FHSA": "FHSA",
        "RRSP": "RRSP",
        "TFSA": "tax_free",
        "Non-registered": "non_registered",
        "Personal": "non_registered"
    }

    account = account_types.get(account, "Unknown_account")
    
    broker = "wealthsimple"
    portfolio_obj = None
    
    # for User to save his transcation 
    user = User.objects.get(username='admin')
    # user portfolio 
    portfolio_obj, created = Portfolio.objects.get_or_create(
        account_type = account, name = broker, user=user)
    
    # creating Stock obj
    stock_obj, created = Stock.objects.get_or_create(
        symbol = symbol
    )

    transaction_types = {
        'Dividend Reinvestment': "DR",
        'Sell': "SL",
        'Buy': "BY"
    }

    transaction_type = transaction_types.get(type_, "unknow_type")

    if Transaction.objects.filter(email_id=email_id).exists():
        return
    obj, created = Transaction.objects.get_or_create(
        email_id = email_id, portfolio = portfolio_obj, stock = stock_obj,
        quantity = float(shares), price = decimal.Decimal(avg_price),
        total_price = decimal.Decimal(total_cost),
        transaction_type = transaction_type, user = user,
        transaction_date = time
    )
    # submit_transaction(self, portfolio, stock, quantity, price, transaction_type, user):
    if created:
        PortfolioItem.objects.submit_transaction(
            portfolio_obj, stock_obj, float(shares), decimal.Decimal(avg_price),
            transaction_type, user
        )
    
    ###
    # to do this we can use observer/strategy pattern here
    # like we fixed "tsly" stock simler we have to adject "qqqy" for 
    # all account ###
    # '19116cbbd5b69469', 
    if email_id == "18e2dec0afed1a00":
        update_portfolio_items()
    elif email_id == '19116cbbd5b69469':
        update_defiance_stocks()
        # item = PortfolioItem.objects.get(
        #     stock__symbol = "TSLY", portfolio__account_type="tax_free")
        # val = item.quantity / 2
        # price = item.purchase_price * 2
        # item.quantity = round(val, 4)
        # item.purchase_price = round(price, 4)
        # item.save()

        # item_2 = PortfolioItem.objects.get(
        #     stock__symbol = "TSLY", portfolio__account_type="FHSA")
        # val_2 = item_2.quantity / 2
        # price_2 = item_2.purchase_price * 2
        # item_2.purchase_price = round(price_2, 4)
        # item_2.quantity = round(val_2, 4)
        # item_2.save()
    # to stop the program when you already saved to database
    if obj and not created:
        print("Saved to database.")


