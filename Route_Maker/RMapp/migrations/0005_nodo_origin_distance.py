# Generated by Django 4.2.2 on 2023-07-13 06:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('RMapp', '0004_nodo_has_route_route_origin'),
    ]

    operations = [
        migrations.AddField(
            model_name='nodo',
            name='origin_distance',
            field=models.DecimalField(decimal_places=8, default=0, max_digits=18),
            preserve_default=False,
        ),
    ]