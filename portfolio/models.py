from django.db import models
from django.contrib.auth.models import User
import locale
import decimal
locale.setlocale( locale.LC_ALL, '' )
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.db.models.signals import pre_save
import datetime

from dividend_goal.models import DividendGoal
from main.utils import find_dividend_received_monthly
# from transaction.models import Transaction
# from portfolioitem.models import PortfolioItem

class Portfolio(models.Model):
    name = models.CharField(max_length=255) #broker name (ex. Wealthsimple)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    total_deposited = models.IntegerField(default=0, blank=True, null=True)
    # account = models.ForeignKey(Account, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=255)
    account_type_choices = [
        ('personal', 'Personal'),
        ('tax_free', 'Tax-Free'),
        ('non_registered', 'Non-Registered'),
        ('FHSA', 'First Home Saving Account'),
        ('RRSP', 'Retirement Account'),
        ('unknown', 'Unknown')
    ]
    account_type = models.CharField(max_length=15, choices=account_type_choices)
    # can calculate total holding in each portfolio eg TFSA, Personal

    def __str__(self) -> str:
        return self.name + ", Account: " + str(self.account_type)
    
    def total_dividend_recived_data(self, user):
        transcations = self.transaction_set.filter(
            user = user, portfolio = self, transaction_type = "DR")
        
        data = find_dividend_received_monthly(transcations)
        return data
        

    
    def portfolio_gain_or_loss_and_holdings(self, user, portfolio):
        data = self.gain_and_lose(user, portfolio)
        total = 0
        for symbol in data:

            total = total + (data[symbol]["avgprice"] * decimal.Decimal(data[symbol]["stocks"])) + data[symbol]["profit"]
        return locale.currency(total, grouping=True)
    
    def gain_and_lose(self, user, portfolio):
        # transactions = Transaction.objects.select_related("stock"
        #     ).filter(user = user, portfolio = portfolio)
        
        transactions = self.transaction_set.select_related("stock"
            ).filter(user = user, portfolio = portfolio)
        data = {}
        for tran in transactions:
            if tran.stock.symbol in data:
                stocks = data[tran.stock.symbol]["stocks"]
                profit = data[tran.stock.symbol]["profit"]
                avg_price = data[tran.stock.symbol]["avgprice"]

                tran_price = tran.price
                if tran.stock.currency == "USD":
                    tran_price = tran.price * decimal.Decimal(1.34)
                tran_stocks = tran.quantity
                tran_type = tran.transaction_type
                
                if tran_type == "BY" or tran_type == "DR":
                    prev_total = avg_price * decimal.Decimal(stocks)
                    current_total = tran_price * decimal.Decimal(tran_stocks)
                    total_share = stocks + tran_stocks
                    avg_cost_per_share = (prev_total + current_total) / decimal.Decimal(total_share)
                    data[tran.stock.symbol]['stocks'] = total_share
                    data[tran.stock.symbol]['avgprice'] = avg_cost_per_share
                elif tran_type == "SL":
                    # profit = sell price - price * sell stocks
                    # profit = old_profit - curr_profit
                    # stocks = stocks - sell stocks
                    gain_or_loss = (tran.price - avg_price) * decimal.Decimal(tran.quantity)
                    final_gain_or_loss = profit + gain_or_loss
                    data[tran.stock.symbol]["profit"] = final_gain_or_loss
                    data[tran.stock.symbol]["stocks"] = stocks - tran.quantity
            else:
                tran_price = tran.price
                if tran.stock.currency == "USD":
                    tran_price = tran.price * decimal.Decimal(1.34)

                data[tran.stock.symbol] = {
                    "stocks": tran.quantity, "profit": 0, "avgprice": tran_price
                }
        # print("!!!!!!!!!!!!!!!!!!!!!!!!", data)
        return data
    
    def stock_DRIP(self, stock):
        portfolio_item = self.portfolioitem_set.get(stock = stock) # PortfolioItem.objects.get(stock = stock)
        # get Transaction related to stock (td.to)
        # calculate drft for that stock
        # in order to calculate DRIP must pay attenation to pay_period

    def holding_amount(self):
        total = 0
        for item in self.portfolioitem_set.all():
            total += item.total_amount()
        return locale.currency(total, grouping=True )
    
    def portfolio_items_information(self):
        dic = {}
        items = self.portfolioitem_set.all()
        performance = self.performance_of_items(items)

        dic['count'] = self.number_of_items(items)
        dic['total_amount'] = round(self.total_amount_of_items(items), 2)
        dic['gain_n_loss'] = round(performance[0], 2)
        dic['percentage'] = round(performance[1], 2)
        
        return dic

    def total_amount_of_items(self, portfolio_items):
        total = 0
        for item in portfolio_items:
            total += item.total_amount()
        # return round(total, 2)
        return total

    def total_curr_amountOf_items(self, items):
        total = 0
        for item in items:
            total += item.capital_amount()
        # return round(total, 2)
        return total

    def all_items_capital(self):
        dolar = 0
        percentages = 0
        count = 0
        f_dollar_amount = 0
        f_pct_amount = 0
        for item in self.portfolioitem_set.all():
            value = item.calculate_profit()
            if value is not None:
                dolar += value['dol']
                percentages += value['pct']
                count += 1
            else:
                pass
        if count:
            f_dollar_amount = dolar
            f_pct_amount = percentages / count

        return {'dol': locale.currency(f_dollar_amount), 'pct': f_pct_amount}
    
    def number_of_items(self, items):
        return items.count()

    def performance_of_items(self, items):
        curr_price_total = self.total_curr_amountOf_items(items)
        pur_price_total = self.total_amount_of_items(items)

        capital = (curr_price_total - pur_price_total)
        percentage = capital / pur_price_total * 100
        return [capital, percentage]

def pre_save_portfolio_slug(sender, instance, *args, **kwargs):
    slug = slugify(instance.name)
    instance.slug = slug
pre_save.connect(pre_save_portfolio_slug, sender=Portfolio)
