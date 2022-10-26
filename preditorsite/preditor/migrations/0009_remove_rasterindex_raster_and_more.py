# Generated by Django 4.0 on 2022-10-15 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('preditor', '0008_raster_satelite_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rasterindex',
            name='raster',
        ),
        migrations.RemoveField(
            model_name='tipoitemformula',
            name='raster',
        ),
        migrations.AddField(
            model_name='raster',
            name='formula',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='raster',
            name='isIndex',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='raster',
            name='url',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.DeleteModel(
            name='ItemFormula',
        ),
        migrations.DeleteModel(
            name='RasterIndex',
        ),
        migrations.DeleteModel(
            name='TipoItemFormula',
        ),
    ]