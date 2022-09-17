from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class GroupURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.not_author = User.objects.create_user(username='not_author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Описание',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            pub_date='Дата публикации',
            group=cls.group,
            id='1',
        )

        cls.guest_client = Client()
        cls.authorized_auth = Client()
        cls.authorized_auth.force_login(cls.author)
        cls.authorized_not_auth = Client()
        cls.authorized_not_auth.force_login(cls.not_author)

    def test_guest_urls_correct_adress_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.author.username}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}): 'posts/post_detail.html',
        }
        for address, template in url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK, template)

    def test_create_correct_address_template(self):
        """URL-адрес создания поста использует соответствующий шаблон"""
        url_names = {
            '/create/': 'posts/create_post.html',
        }
        for address in url_names.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=False)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                response = self.authorized_not_auth.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        for address, template in url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertTemplateUsed(response, 'users/login.html')
                response = self.authorized_not_auth.get(address)
                self.assertTemplateUsed(response, template)

    def test_create_correct_address_template(self):
        """URL-адрес редактирования поста использует соответствующий шаблон"""
        url_names = {
            '/posts/1/edit/': 'posts/create_post.html',
        }
        for address in url_names.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=False)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                response = self.authorized_not_auth.get(address, follow=True)
                self.assertRedirects(response, '/posts/1/')
                response = self.authorized_auth.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        for address, template in url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertTemplateUsed(response, 'users/login.html')
                response = self.authorized_not_auth.get(address, follow=True)
                self.assertTemplateUsed(response, 'posts/post_detail.html')
                response = self.authorized_auth.get(address)
                self.assertTemplateUsed(response, template)

    def test_follow_address_template(self):
        """URL-адрес подписки поста использует соответствующий шаблон"""
        url_names = {
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for address, template in url_names.items():
            with self.subTest(address=address):
                response = self.authorized_auth.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK, template)
                response = self.guest_client.get(address, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK, 'users/login.html') 