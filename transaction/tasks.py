from celery import shared_task
from transaction.scrape_emails import GmailAnalyzer
from transaction.models import Transaction
from portfolioitem.models import PortfolioItem
from portfolio.models import Portfolio
from stocks.models import Stock
import decimal
from django.contrib.auth.models import User


@shared_task
def process_gmail_emails():
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    gmail_analyzer = GmailAnalyzer(SCOPES)
    messages = gmail_analyzer.fetch_emails()
    for msg in messages:
        email_data = gmail_analyzer.get_email_data(gmail_analyzer.service, msg)
        if email_data:
            email_info = gmail_analyzer.process_email(email_data)
            print(email_info)
            # if email_info:
                # stop_flag = save_to_database(email_info)

def save_to_database(emails):

    email_id = emails['id'].strip()
    account = emails['account'].strip()
    shares = emails['shares'].strip()
    avg_price = emails['avg_price'].strip()
    total_cost = emails['total_cost'].strip()
    symbol = emails['symbol'].strip()
    type_ = emails['type'].strip()
    time = emails['time']

    sr_value = ""
    if "FHSA" in account:
        sr_value = "FHSA"
    elif "TFSA" in account:
        sr_value = 'tax_free'
    elif "Non-registered" in account:
        sr_value = 'non_registered'
    elif "Personal" in account:
        sr_value = 'non_registered'
    else:
        # raise error (because we can't find the profolio)
        pass
    broker = "wealthsimple"
    portfolio_obj = None
    
    # portfolio_obj = Portfolio.objects.filter(account_type = sr_value, name = broker)[:0]
    # if not portfolio_obj:
    #     portfolio_obj = Portfolio.objects.create(account_type = sr_value, name = broker)
    # print(portfolio_obj)
    user = User.objects.get(username='admin')
    portfolio_obj, created = Portfolio.objects.get_or_create(
        account_type = sr_value, name = broker, user=user)
    
    stock_obj, created = Stock.objects.get_or_create(
        symbol = symbol
    )
    acc_type = ""
    if 'Dividend Reinvestment' in type_:
        acc_type = "DR"
    elif 'Sell' in type_:
        acc_type = "SL"
    elif 'Buy' in type_:
        acc_type = "BY"

    obj, created = Transaction.objects.get_or_create(
        email_id = email_id, portfolio = portfolio_obj, stock = stock_obj,
        quantity = float(shares), price = decimal.Decimal(avg_price),
        total_price = decimal.Decimal(total_cost),
        transaction_type = acc_type, user = user,
        transaction_date = time
    )
    # submit_transaction(self, portfolio, stock, quantity, price, transaction_type, user):
    if created:
        PortfolioItem.objects.submit_transaction(
            portfolio_obj, stock_obj, float(shares), decimal.Decimal(avg_price),
            acc_type, user
        )
    # to stop the program when you already saved to database
    if obj and not created:
        print("Saved to database.")
        

@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y
