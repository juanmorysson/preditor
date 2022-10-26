# Generated by Django 4.0 on 2022-09-28 11:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('preditor', '0005_area'),
    ]

    operations = [
        migrations.CreateModel(
            name='Modelo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pasta', models.CharField(max_length=20, unique=True)),
                ('descricao', models.CharField(max_length=200)),
                ('data_criacao', models.DateTimeField(blank=True, null=True)),
                ('responsavel', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
            ],
        ),
    ]