# Generated by Django 2.2.16 on 2022-09-11 14:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20220805_2249'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, upload_to='posts/', verbose_name='Картинка'),
        ),
        migrations.AlterField(
            model_name='group',
            name='description',
            field=models.TextField(help_text='Описание группы', max_length=500, verbose_name='Описание'),
        ),
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.SlugField(help_text='Придумайте адрес для группы. Используйте только латиницу, цифры, дефисы и знаки подчёркивания', unique=True, verbose_name='Адрес для страницы группы'),
        ),
        migrations.AlterField(
            model_name='group',
            name='title',
            field=models.CharField(help_text='Придумайте название', max_length=200, verbose_name='Название группы'),
        ),
        migrations.AlterField(
            model_name='post',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='posts', to='posts.Group', verbose_name='Группа'),
        ),
        migrations.AlterField(
            model_name='post',
            name='text',
            field=models.TextField(help_text='Напишите пост', verbose_name='Текст поста'),
        ),
    ]
