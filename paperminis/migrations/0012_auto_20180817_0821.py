# Generated by Django 2.1 on 2018-08-17 06:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paperminis', '0011_auto_20180816_1356'),
    ]

    operations = [
        migrations.AlterField(
            model_name='printsettings',
            name='paper_format',
            field=models.CharField(choices=[('a4', 'A4'), ('a3', 'A3'), ('letter', 'Letter'), ('legeal', 'Legal'), ('tabloid', 'Tabloid')], default='a4', max_length=50),
        ),
    ]
