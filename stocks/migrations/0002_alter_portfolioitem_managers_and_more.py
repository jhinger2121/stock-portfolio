# Generated by Django 4.2 on 2023-05-01 01:03

from django.db import migrations, models
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='portfolioitem',
            managers=[
                ('manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterField(
            model_name='portfolioitem',
            name='purchase_date',
            field=models.DateField(auto_now_add=True),
        ),
    ]
