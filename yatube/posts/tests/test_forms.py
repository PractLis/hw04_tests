from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Тестовое описание'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_correct_create_post(self):
        """Проверка создания нового поста авторизованным пользователем."""
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True,
        )
        post_1 = Post.objects.get(id=self.group.id)
        author_1 = User.objects.get(username=self.author.username)
        group_1 = Group.objects.get(title='Тестовый заголовок')
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse
                             ('posts:profile',
                              kwargs={'username': self.author.username}
                              )
                             )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post_1.text, form_data['text'])
        self.assertEqual(author_1.username, self.author.username)
        self.assertEqual(group_1.title, self.group.title)

    def test_correct_edit_post(self):
        """Проверка редактирования поста авторизованным пользователем."""
        form_data = {
            'text': 'Тестовый текс',
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True,
        )
        changed_post = Post.objects.get(id=self.group.id)
        self.client.get(f'/{self.author}/{changed_post.id}/edit/')
        form_data = {
            'text': 'Новый текст',
            'group': self.group.id
        }
        response_edit = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={
                        'post_id': changed_post.id,
                    }),
            data=form_data,
            follow=True,
        )
        changed_post = Post.objects.get(id=self.group.id)
        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        self.assertEqual(changed_post.text, 'Новый текст')

    def test_guest_create_post(self):
        """Проверка создания нового поста гостем."""
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Тестовый текс',
            'group': self.group.id
        }
        response = self.guest_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=False,
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Post.objects.count(), count_posts)
        self.assertFalse(Post.objects.filter(
            text='Тестовый текс').exists())

    def test_guest_edit_post(self):
        """Проверка редактирования нового поста гостем."""
        form_data = {
            'text': 'Тестовый текс',
            'group': self.group.id
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': '1'}),
            data=form_data,
            follow=False
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
