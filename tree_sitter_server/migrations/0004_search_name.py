# Generated by Django 3.2.13 on 2022-05-21 06:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('syntaxforest', '0003_search_create_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='search',
            name='name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
