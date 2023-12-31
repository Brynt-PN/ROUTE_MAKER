# Generated by Django 4.2.2 on 2023-07-13 03:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('RMapp', '0003_alter_nodo_quadrant'),
    ]

    operations = [
        migrations.AddField(
            model_name='nodo',
            name='has_route',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='route',
            name='origin',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='relational_route', to='RMapp.origin'),
            preserve_default=False,
        ),
    ]
