# Generated by Django 2.1.3 on 2019-12-10 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paperminis', '0015_printsettings_darken'),
    ]

    operations = [
        migrations.AddField(
            model_name='printsettings',
            name='force_name',
            field=models.CharField(choices=[('no_force', 'Leave it to the Creature (default)'), ('force_name', 'Force printing of all names'), ('force_blank', 'Force printing no names')], default='no_force', max_length=50),
        ),
    ]
