# Generated by Django 4.2.3 on 2023-12-31 22:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0018_alter_transaction_transaction_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='stock_yield',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
