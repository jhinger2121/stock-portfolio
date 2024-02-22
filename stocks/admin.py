from django.contrib import admin
from transaction.models import Transaction
from portfolioitem.models import PortfolioItem
from portfolio.models import Portfolio
from stocks.models import Stock
class AccountAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

class PortfolioAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Stock)
# admin.site.register(Account, AccountAdmin)
admin.site.register(Portfolio, PortfolioAdmin)
admin.site.register(PortfolioItem)
admin.site.register(Transaction)