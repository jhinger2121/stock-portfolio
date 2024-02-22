from django.db import models
from django.contrib.auth.models import User
from stocks.models import Stock


class WatchList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=155)
    stocks = models.ManyToManyField(Stock)

    def __str__(self):
        return self.name

