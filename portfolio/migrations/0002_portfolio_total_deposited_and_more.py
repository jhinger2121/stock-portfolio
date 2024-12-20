# Generated by Django 4.2.3 on 2024-06-08 00:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='portfolio',
            name='total_deposited',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='portfolio',
            name='account_type',
            field=models.CharField(choices=[('personal', 'Personal'), ('tax_free', 'Tax-Free'), ('non_registered', 'Non-Registered'), ('FHSA', 'First Home Saving Account'), ('RRSP', 'Retirement Account'), ('unknown', 'Unknown')], max_length=15),
        ),
    ]
