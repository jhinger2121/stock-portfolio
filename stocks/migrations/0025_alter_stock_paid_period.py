# Generated by Django 4.2.3 on 2024-01-19 12:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0024_alter_stock_yahoo_ticker_symbol'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='paid_period',
            field=models.CharField(choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly')], default='monthly', max_length=10),
        ),
    ]
