from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.conf import settings
import decimal
import datetime
import locale
locale.setlocale( locale.LC_ALL, '' )

from stocks.models import Stock
from portfolio.models import Portfolio

    
class PortfolioItemManager(models.Manager):
    def submit_transaction(self, portfolio, stock, quantity, price, transaction_type, user):
        try:
            portfolio_item = self.get(stock = stock, portfolio = portfolio)
            if portfolio_item:
                if transaction_type == 'DR':
                    portfolio_item.total_dividend_paied += price

                if transaction_type == 'BY' or transaction_type == 'DR':
                    prev_total = portfolio_item.purchase_price * decimal.Decimal(portfolio_item.quantity)
                    current_total = price * decimal.Decimal(quantity)
                    total_share = quantity + portfolio_item.quantity
                    
                    avg_cost_per_share = (prev_total + current_total) / decimal.Decimal(total_share)

                    portfolio_item.purchase_price = avg_cost_per_share

                    portfolio_item.quantity = total_share
                    portfolio_item.save()
                else:
                    stock_qty = portfolio_item.quantity - quantity
                    portfolio_item.quantity = stock_qty
                    if stock_qty < 0.009:
                        portfolio_item.delete()
                    else:
                        portfolio_item.save()
        except PortfolioItem.DoesNotExist:
            portfolio_item = self.create(
                portfolio=portfolio, stock=stock, quantity=quantity,
                purchase_price=price, user = user
            )


    def get_total_holding_amount(self, portfolio):
        total_holding_amount = 0

        portfolio_items = self.filter(portfolio = portfolio)

        for item in portfolio_items:
            price = item.purchase_price
            if item.current_price is not None:
                price = item.current_price
            holding_amount = item.quantity * price
            total_holding_amount += holding_amount
        return total_holding_amount


class PortfolioItem(models.Model):
    """ PortfolioItem is a model that represents an individual stock or 
    investment that is held in a user's investment portfolio."""
    CURRENCYS = [
        ('CAD', 'CAD'),
        ('USD', 'USD'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)

    quantity = models.FloatField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=4)
    purchase_date = models.DateField(auto_now_add=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    currency = models.CharField(choices = CURRENCYS, max_length = 5, default="CAD")
    
    total_dividend_paied = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=decimal.Decimal(0.0))
    commission = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    objects = PortfolioItemManager()

    def __str__(self) -> str:
        return self.stock.symbol + ", Portfolio: " + self.portfolio.account_type
    
    def total_return_percentage(self):
        if not self.current_price or self.quantity <= 0:
            return 0

        # Adjust dividend based on currency
        dividend = self.total_dividend_paied or decimal.Decimal(0.0)  # Avoid None issues
        if self.currency == 'USD':
            dividend *= decimal.Decimal(settings.CAD_TO_USD)

        # Net purchase price for the entire position
        total_purchase_price = self.purchase_price * decimal.Decimal(self.quantity)

        # Net current value for the entire position
        total_current_value = self.current_price * decimal.Decimal(self.quantity)

        # Calculate total return: 
        # ((Current Value + Total Dividend) - Total Purchase Price) / Total Purchase Price
        if total_purchase_price > 0:
            val = (total_current_value + dividend - total_purchase_price) / total_purchase_price
        else:
            val = 0  # Handle case where purchase price is zero to avoid division by zero

        return round(val * 100, 2)  # Return as percentage

    def total_return_amount(self):
        if not self.current_price or self.quantity <= 0:
            return 0

        # Adjust dividend based on currency
        dividend = self.total_dividend_paied or decimal.Decimal(0.0)
        if self.currency == 'USD':
            dividend *= decimal.Decimal(settings.CAD_TO_USD)

        # Net purchase price for the entire position
        total_purchase_price = self.purchase_price * decimal.Decimal(self.quantity)

        # Net current value for the entire position
        total_current_value = self.current_price * decimal.Decimal(self.quantity)

        total_return_amount = (total_current_value + dividend) - total_purchase_price
        return round(total_return_amount, 2)
    
    def DRIP_table(self):
        # ROws
        # ticker      holding       current DRIP   		changes to DRIP     
        # CALL        stock		dividend month/quater	stock buy
        #             amount		stock can buy			amount to bought
        stock_DRIPs = {}

        # Row 1 (stock info)
        stock_DRIPs['stock'] = {'ticker': self.stock.symbol, 'name': self.stock.name}

        # row 2 (holding)
        stock_DRIPs['holding'] = {'stocks': self.quantity, 'amount': self.total_amount()}

        # row3 (distribution)
        dividend = self.dividend_earning()
        stocks_can_buy = None
        if not self.stock.price or not dividend:
            stocks_can_buy = "Missing stock data."
        else:
            stocks_can_buy = float(dividend / self.stock.price)
            stock_DRIPs['distribution'] = {
                'dividend': round(dividend, 2),
                'stocks_can_buy': stocks_can_buy
            }
        # row 4 (Changes to DRIPs)
        if isinstance(stocks_can_buy, float):
            # "+1" is for to earn extra stock from dividend
            stocks_can_buy_now = int(stocks_can_buy) + 1
            DRIPs_single = self.stock.price / self.stock.distribution_per_share

            # here "+1" to make sure we earn enough to own "stocks_can_buy"
            stocks_should_own = int(DRIPs_single * stocks_can_buy_now) + 1

            dividend_now = decimal.Decimal(stocks_should_own * self.stock.distribution_per_share)
            stocks_add = stocks_should_own - self.quantity
            amount_add = decimal.Decimal(stocks_add) * self.stock.price

            stock_DRIPs['change'] = {
                'stocks': stocks_add, 'dividend': dividend_now,
                'stocks_can_buy': stocks_can_buy_now, 'total_stocks': stocks_should_own,
                'amount_add': amount_add
            }
        else:
            stock_DRIPs['change'] = {
                "error": stocks_can_buy
            }
            
        return stock_DRIPs                                                   
    
    def dividend_by_months(self, months):
        dividend_list = []
        stocks = decimal.Decimal(self.quantity)

        if not self.stock.paid_period or not self.stock.distribution_per_share:
            strr = f"Missing some data for '{self.stock}' to calculate dividend."
            return [{"message": self.stock.symbol}]

        for i in range(months):
            today = datetime.date.today()

            curr_month = today + datetime.timedelta(days=31*i)
            if self.stock.paid_period == "monthly":
                dividend_earned = stocks * self.stock.distribution_per_share
                dividend_list.append(
                    {"dividend": dividend_earned, 'month': curr_month.strftime('%B')}
                )
            if self.stock.paid_period == "quarterly":

                if not self.stock.previous_payout_date or not self.stock.upcoming_payout_date:
                    strr = f"Missing 'Payment Date' for '{self.stock}'."
                    return [{"message": strr}]
                
                date = self.stock.upcoming_payout_date
                chk_pay_period = []
                if date.month in [1, 4, 7, 10]:
                    chk_pay_period = [1, 4, 7, 10]
                elif date.month in [2, 5, 8, 11]:
                    chk_pay_period = [2, 5, 8, 11]
                elif date.month in [3, 6, 9, 12]:
                    chk_pay_period = [3, 6, 9, 12]

                if curr_month.month in chk_pay_period:
                    dividend_earned = stocks * self.stock.distribution_per_share
                    dividend_list.append(
                        {"dividend": dividend_earned, 'month': curr_month.strftime('%B')}
                    )
                else:
                    dividend_list.append(
                        {"dividend": 0, 'month': curr_month.strftime('%B')}
                    )
        return dividend_list
        
    def calculate_DRIP(self, year_long):
        if not self.stock.paid_period or not self.stock.distribution_per_share:
            return []
        
        month_count = 0
        left_over = 0
        dividend_left = 0
        stocks = decimal.Decimal(self.quantity)
        dividend_list = []
        for i in range(year_long):
            if self.stock.paid_period == "quarterly":
                for i in range(1, 13):
                    month_count += 1
                    if month_count == 3:
                        month_count = 0
                        div_earning = stocks * self.stock.distribution_per_share

                        if dividend_left:
                            div_earning += dividend_left

                        if div_earning >= self.purchase_price:
                            stk = int(div_earning / self.purchase_price)
                            dividend_left = div_earning % self.purchase_price
                            stocks += decimal.Decimal(stk)

                            total_amount = stocks * self.purchase_price
                            total_amount += dividend_left

                            dividend_list.append(
                                {'amount': total_amount, 'left': 0}
                            )
                        else:
                            total_amount = stocks * self.purchase_price
                            total_amount = total_amount + div_earning + dividend_left
                            dividend_left += div_earning

                            dividend_list.append(
                                {'amount': total_amount, 'left': 0}
                            )
                    else:
                        # added dic to dividend_list because i also want to add
                        # left over amount dividend, try to set {'left': 0} to zero
                        # and refresh graph to see what it messes up
                        dividend_list.append(
                            {'amount': stocks * self.purchase_price, 'left': dividend_left}
                        )
            if self.stock.paid_period == "monthly":
                for i in range(1, 13):
                    div_earning = stocks * self.stock.distribution_per_share

                    if dividend_left:
                        div_earning += dividend_left

                    if div_earning >= self.purchase_price:
                        stk = int(div_earning / self.purchase_price)
                        dividend_left = div_earning % self.purchase_price
                        stocks += decimal.Decimal(stk)
                        total_amount = stocks * self.purchase_price
                        total_amount += dividend_left

                        dividend_list.append(
                            {'amount': total_amount, 'left': dividend_left}
                        )
                    else:
                        total_amount = stocks * self.purchase_price
                        total_amount = total_amount + div_earning + dividend_left
                        dividend_left += div_earning

                        dividend_list.append(
                            {'amount': total_amount, 'left': 0}
                        )

        return dividend_list
                    
    def update_current_price(self, price):
        # Get current price of stock from an external API and update the current_price field
        # You can use a library like requests or urllib to make the API call
        self.current_price = price
        self.save()

    def annual_dividend_earning(self):
        ann_dividend = self.annual_dividend()
        if "no_data" in ann_dividend:
            return ann_dividend # returns {"no_data": "Not enough data to show."} line: 433
        data = ann_dividend['data'] * decimal.Decimal(self.quantity)
        return {'data': data}
    
    def annual_dividend(self):
        dividend = self.stock.distribution_per_share
        pay_period = self.stock.paid_period

        if not (dividend and pay_period):
            return {"no_data": "Not enough data to show."}
        value = 0
        if pay_period == "monthly":
            value = dividend * 12
        elif pay_period == "weekly":
            value = dividend * decimal.Decimal(52.1429)
        else:
            value = dividend * 4
        
        return {'data': value}
            

    def purch_price(self):
        return round(self.purchase_price, 2)
    
    def curr_price(self):
        if not self.current_price:
            return 0
        return round(self.current_price, 2)
    
    def calculate_profit(self):
        if self.current_price is not None:
            dol = (self.current_price - self.purchase_price) * \
                decimal.Decimal(self.quantity)
            pct = (self.current_price - self.purchase_price) / self.purchase_price
            profit_pct = pct * 100
            return {'dol': round(dol, 2), 'pct': round(profit_pct, 2)}
        else:
            return None
        
    def total_amount(self):
        price = None
        if self.current_price:
            price = self.current_price
        elif self.current_price and self.currency == "USD":
            price = self.current_price * decimal.Decimal(settings.CAD_TO_USD)
        else:
            price = self.purchase_price
        value = price * decimal.Decimal(self.quantity)
        return {"show": locale.currency(value, grouping=True), 
                "value": round(value, 4)}
    
    def qty(self):
        return round(self.quantity, 4)
    
    def capital_amount(self):
        if self.current_price:
            return round(self.current_price * decimal.Decimal(self.quantity), 2)
        return round(self.purchase_price * decimal.Decimal(self.quantity), 2)
    
    def amount_invested(self):
        return round(self.purchase_price * decimal.Decimal(self.quantity), 2)
    
    def dividend_earning(self):
        if not self.stock.distribution_per_share:
            return None
        return decimal.Decimal(self.quantity) * self.stock.distribution_per_share
    

@receiver(post_save, sender=PortfolioItem)
def update_commission(sender, instance, **kwargs):
    if instance.pk:
        old_currency = PortfolioItem.objects.filter(pk=instance.pk).values('currency').first().get('currency')
        if old_currency != instance.currency:
            if instance.currency == 'USD':
                instance.commission = decimal.Decimal(0.15)
