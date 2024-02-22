from django.db import models
from django.contrib.auth.models import User
from django.db.models.query import QuerySet

from stocks.models import Stock
from portfolio.models import Portfolio
from portfolioitem.models import PortfolioItem

# Create your models here.
class TransactionQuerySet(models.QuerySet):
    def latest(self):
        return self.order_by("-pk")
    
class TransactionManager(models.Manager):
    def get_queryset(self):
        return TransactionQuerySet(self.model, using=self._db)
    
    def latest_15(self):
        return self.get_queryset().latest()[:15]
    
    def calculate_loss_n_gain(self, user, portfolio):
        transactions = Transaction.objects.filter(user = user, portfolio = portfolio)
        data = {"stock": {"id": "TD.un", "profoit": 0}}
        print(transactions)
        for stock in transactions:
            pass

class Transaction(models.Model):
    email_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)

    quantity = models.FloatField()
    price = models.DecimalField(max_digits=10, decimal_places=4)
    total_price = models.DecimalField(max_digits=10, decimal_places=4)
    transaction_date = models.DateTimeField()
    transaction_type_choices = [
        ('BY', 'Market Buy'),
        ('SL', 'Market Sell'),
        ('DR', "Dividend Reinvestment Buy")
    ]
    transaction_type = models.CharField(max_length=2, choices=transaction_type_choices)
    # commission = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    objects = TransactionManager()
    # ording -pk is messing with the total of portfolio 
    # class Meta:
    #     ordering = ["-pk"]

    def __str__(self) -> str:
        return self.stock.symbol + ", Price: " + str(self.price) + ", Type: " + str(self.transaction_type) + ", Account: " + str(self.portfolio) + ", Account: " + str(self.transaction_date)
    
    
    # def save(self, *args, **kwargs):
    #     print(self.transaction_type, "!!!!!!!!!!!!!!")
    #     PortfolioItem.objects.submit_transaction(
    #         self.portfolio, self.stock, self.quantity, self.price, self.transaction_type, self.user
    #     )
    #     super().save(*args, **kwargs)