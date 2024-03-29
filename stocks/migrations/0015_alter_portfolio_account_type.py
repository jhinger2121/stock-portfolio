# Generated by Django 4.2.3 on 2023-10-27 03:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0014_alter_transaction_transaction_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='portfolio',
            name='account_type',
            field=models.CharField(choices=[('personal', 'Personal'), ('tax_free', 'Tax-Free'), ('non-registered', 'Non-Registered'), ('FHSA', 'First Home Saving Account'), ('unknown', 'Unknown')], max_length=15, unique=True),
        ),
    ]
