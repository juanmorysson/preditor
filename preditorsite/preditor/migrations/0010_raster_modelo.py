# Generated by Django 4.0 on 2022-10-15 16:20

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('preditor', '0009_remove_rasterindex_raster_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Raster_Modelo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_criacao', models.DateTimeField(default=django.utils.timezone.now)),
                ('modelo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='preditor.modelo')),
                ('raster', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='preditor.raster')),
            ],
        ),
    ]
