# Generated by Django 3.2.13 on 2022-05-20 08:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paperminis', '0020_auto_20220503_1646'),
    ]

    operations = [
        migrations.AddField(
            model_name='creature',
            name='background_color',
            field=models.CharField(choices=[('228b22', 'Green'), ('aa3939', 'Red'), ('005b96', 'Blue'), ('d3d3d3', 'Light Gray'), ('a9a9a9', 'Dark Gray'), ('000000', 'Black'), ('ffffff', 'White')], default='ffffff', max_length=6),
        ),
    ]
