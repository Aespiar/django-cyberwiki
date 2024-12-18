# Generated by Django 5.0.9 on 2024-11-29 22:55

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Personal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('turno', models.CharField(max_length=100)),
                ('rol', models.CharField(max_length=100)),
                ('imagen', models.ImageField(default='avatar.png', upload_to='avatars/')),
            ],
            options={
                'db_table': 'main_menu_personal',
            },
        ),
    ]
