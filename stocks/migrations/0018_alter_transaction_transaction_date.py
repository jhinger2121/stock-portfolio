# Generated by Django 4.2.3 on 2023-12-11 07:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0017_portfolioitem_user_transaction_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='transaction_date',
            field=models.DateTimeField(),
        ),
    ]
