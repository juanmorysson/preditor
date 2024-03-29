# Generated by Django 4.0 on 2022-03-04 20:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('preditor', '0002_barraprogresso'),
    ]

    operations = [
        migrations.AddField(
            model_name='barraprogresso',
            name='data_criacao',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='barraprogresso',
            name='data_finalizacao',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='barraprogresso',
            name='processo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='preditor.projeto'),
        ),
        migrations.AddField(
            model_name='barraprogresso',
            name='usuario',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='auth.user'),
        ),
    ]
