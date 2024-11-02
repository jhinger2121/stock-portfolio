# Generated by Django 4.2.3 on 2024-10-05 12:55

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolioitem', '0002_portfolioitem_commission_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='portfolioitem',
            name='total_dividend_paied',
            field=models.DecimalField(blank=True, decimal_places=2, default=Decimal('0'), max_digits=10, null=True),
        ),
    ]
