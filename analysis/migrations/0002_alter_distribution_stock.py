# Generated by Django 3.2 on 2023-05-08 18:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0004_auto_20230507_1544'),
        ('analysis', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distribution',
            name='stock',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='stocks.stock'),
        ),
    ]