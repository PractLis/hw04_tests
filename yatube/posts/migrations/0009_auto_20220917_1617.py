# Generated by Django 2.2.16 on 2022-09-17 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_follow'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='posts/', verbose_name='Картинка'),
        ),
    ]