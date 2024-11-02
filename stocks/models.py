from django.db import models

import locale
locale.setlocale( locale.LC_ALL, '' )


# NEWS class for stocks to displayed each stock realated news
# create total_holding field in Portfolio class
# cashe the results when data change kill the cashe

              

class Stock(models.Model):
    # only owner can add stock 
    CURRENCYS = [
        ('CAD', 'CAD'),
        ('USD', 'USD'),
    ]
    symbol = models.CharField(max_length=10, unique=True)
    yahoo_ticker_symbol = models.CharField(max_length=10, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    currency = models.CharField(choices = CURRENCYS, max_length = 5, default="CAD")

    pay_period_choices = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]
    
    distribution_per_share = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    stock_yield = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    # x_dividend_date = models.DateField(null=True, blank=True)
    paid_period = models.CharField(
        max_length=10, choices=pay_period_choices, default="monthly"
    )
    upcoming_payout_date = models.DateField(null=True, blank=True)
    previous_payout_date = models.DateField(null=True, blank=True)
    
    def update_information(self, dividend, ex_date, dividend_yield, pay_period, stock_name): 
        self.x_dividend_date = ex_date
        self.distribution_per_share = dividend
        self.stock_yield = dividend_yield
        self.paid_period = pay_period
        self.name = stock_name
        self.save()

    def __str__(self) -> str:
        return self.symbol + " (" + self.symbol + ")"
    
    def save(self, *args, **kwargs):
        self.symbol = self.symbol.upper()
        super().save(*args, **kwargs)
    
    def update_current_price(self, price):
        # Get current price of stock from an external API and update the current_price field
        # You can use a library like requests or urllib to make the API call
        self.price = price
        self.save()

class Xdividend(models.Model):
    x_dividend_date = models.DateField(null=True, blank=True)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)

    # add a restriction so that i cann't add another x dividend
    # date for same month
    def __str__(self) -> str:
        return str(self.x_dividend_date)

