from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Напишите пост'
    )

    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор')

    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Группа'
    )

    class Meta:
        ordering = ('-pub_date',)
        default_related_name = 'post'

    def __str__(self):
        return self.text[:15]


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название группы',
        help_text='Придумайте название',
    )

    slug = models.SlugField(
        null=False,
        unique=True,
        verbose_name='Адрес для страницы группы',
        help_text=('Придумайте адрес для группы. Используйте только '
                   'латиницу, цифры, дефисы и знаки подчёркивания'),
    )

    description = models.TextField(
        max_length=500,
        verbose_name='Описание',
        help_text='Описание группы',
    )

    def __str__(self) -> str:
        return self.title
