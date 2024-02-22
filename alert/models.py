from django.db import models
from django.contrib.auth.models import User
from stocks.models import Stock
from portfolio.models import Portfolio
from portfolioitem.models import PortfolioItem

class AlertQuerySet(models.QuerySet):
    def avg_price(self):
        return self.filter(average_price = True)

class AlertManager(models.Manager):
    def get_queryset(self):
        return AlertQuerySet(self.model, using=self._db)
    
    def check_average_price(self):
        return self.get_queryset().avg_price()
    
    def activate_tracker(self):
        msg_alerts = {}
        alerts = self.all()
        for alert in alerts:
            if alert.average_price:
                msg_alerts["average_price"] = alert.average_price_crossed()
        return msg_alerts

class Alert(models.Model):
    NAME_CHOICES = [
        ("AVG", "Average Price"),
    ]
    category = models.CharField(choices=NAME_CHOICES, max_length=3)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    average_price = models.BooleanField(default=True, null=True, blank=True)

    objects = AlertManager()

    def __str__(self) -> str:
        return self.stock.symbol
    
    def average_price_crossed(self):
        # alert when current price go low than bought price
        msg_list = []
        portfolio_item = PortfolioItem.objects.filter(
            stock=self.stock
        )
        # print(portfolio_item)
        for item in portfolio_item:
            print("!!!!!!!!!!!!",item, item.current_price, item.purchase_price)
            if item.current_price <= item.purchase_price:
                msg = f"""
                Price went down from the average bought price of 
                {self.stock} in your '{item.portfolio}'portfolio.
                """
                msg_list.append(msg)
        return msg_list