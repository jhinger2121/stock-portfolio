from django.db import models

from stocks.models import Stock

# distribution class 
# it can have Stock(foreignkey), distribution per stock(0.12 cents), yield,
#            x-divided date, paid period(monthly, quartly), last_payout_date,
#           upcomoing_payout_date, etc..

# start working on scraper to get the data

class Distribution(models.Model):
    pay_period_choices = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]
    stock = models.OneToOneField(Stock, on_delete=models.CASCADE)
    distribution_per_share = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    stock_yield = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True
    )
    x_dividend_date = models.DateField(null=True, blank=True)
    paid_period = models.CharField(
        max_length=10, choices=pay_period_choices, null=True, blank=True
    )
    upcoming_payout_date = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        return self.stock.name + " (" + self.stock.symbol + ")"
    
    def update_information(self, dividend, ex_date, dividend_yield):
        self.distribution_per_share = dividend
        self.x_dividend_date = ex_date
        self.stock_yield = dividend_yield
        self.save()
