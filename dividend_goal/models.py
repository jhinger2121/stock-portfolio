import decimal
from django.db import models
from django.contrib.auth.models import User


class DividendGoal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    annual_goal = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Dividend Goal"
    
    def get_annual_goal(self):
        return self.annual_goal
    
    # Method to get monthly goal
    def get_monthly_goal(self):
        return self.annual_goal / 12

    # Method to get daily goal (assuming 365 days in a year)
    def get_daily_goal(self):
        return self.annual_goal / 365

    def get_weekly_goal(self):
        return self.annual_goal / decimal.Decimal(52.1429)
    
    def format_as_currency(self, amount):
        return f"${amount:,.2f}" 