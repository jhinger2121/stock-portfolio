from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from transaction.models import Transaction
from portfolioitem.models import PortfolioItem
from portfolio.models import Portfolio
from stocks.models import Stock

class StockForm(ModelForm):
    class Meta:
        model = Stock
        fields = [
            'symbol',
            'name'
        ]
        help_texts = {
            "symbol": _('Symbol must be "Stock exchange:Ticker symbol" - example TSX:TD'),
        }

class TransactionForm(ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'portfolio', 'stock', 'quantity', 'price', 'total_price',
            'transaction_type'
        ]
        