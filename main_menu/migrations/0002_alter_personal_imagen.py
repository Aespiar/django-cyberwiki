# Generated by Django 5.0.9 on 2024-11-30 06:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_menu', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personal',
            name='imagen',
            field=models.ImageField(blank=True, default='avatars/avatar.png', null=True, upload_to='avatars/'),
        ),
    ]