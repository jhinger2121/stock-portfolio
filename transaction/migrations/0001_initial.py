# Generated by Django 4.2.3 on 2024-01-14 08:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('portfolio', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stocks', '0022_remove_portfolioitem_portfolio_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_id', models.CharField(max_length=100, unique=True)),
                ('quantity', models.FloatField()),
                ('price', models.DecimalField(decimal_places=4, max_digits=10)),
                ('total_price', models.DecimalField(decimal_places=4, max_digits=10)),
                ('transaction_date', models.DateTimeField()),
                ('transaction_type', models.CharField(choices=[('BY', 'Market Buy'), ('SL', 'Market Sell'), ('DR', 'Dividend Reinvestment Buy')], max_length=2)),
                ('portfolio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portfolio.portfolio')),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stocks.stock')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]