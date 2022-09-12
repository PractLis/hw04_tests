from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Group, Post

User = get_user_model()

NUMB_OF_POSTS = 13
TEMP_NUMB_FIRST_PAGE = 10
TEMP_NUMB_SECOND_PAGE = 3


class GroupViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
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
        )

        cls.guest_client = Client()
        cls.authorized_auth = Client()
        cls.authorized_auth.force_login(cls.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse('posts:group_list',
                                             kwargs={'slug': 'test-slug'}
                                             ),
            'posts/profile.html': reverse('posts:profile',
                                          kwargs={'username':
                                                  self.author.username}
                                          ),
            'posts/post_detail.html': reverse('posts:post_detail',
                                              kwargs={'post_id': self.post.id}
                                              ),
            'posts/create_post.html': reverse('posts:post_edit',
                                              kwargs={'post_id': self.post.id}
                                              ),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_auth.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_page__correct_template(self):
        templates_pages_names = {
            'posts/create_post.html': reverse('posts:create_post'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_auth.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_auth.get(reverse('posts:index'))
        post_text_0 = response.context['page_obj'][0]
        post_text_0 = {response.context['post'].text: 'Тестовый пост',
                       response.context['post'].group: self.group,
                       response.context['post'].author.username:
                       self.author.username}
        for value, expected in post_text_0.items():
            self.assertEqual(post_text_0[value], expected)

    def test_group_pages_show_correct_context(self):
        """Шаблон Group список постов,  отфильтрованных по группе."""
        response = self.authorized_auth.get(reverse('posts:group_list',
                                            kwargs={'slug': 'test-slug'})
                                            )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertEqual(response.context['group'].title, 'Тестовый заголовок')
        self.assertEqual(post_text_0, 'Тестовый пост')

    def test_profile_correct_context(self):
        """Шаблон profile отфильтрован по пользователю"""
        response = self.authorized_auth.get(reverse
                                            ('posts:profile',
                                             kwargs={'username':
                                                     self.author.username}
                                             ))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertEqual(response.context['author'].username, 'author')
        self.assertEqual(post_text_0, 'Тестовый пост')

    def test_post_detail_correct_context(self):
        """Шаблон post_id с правильным контекстом отфильтрован по id"""
        response = self.authorized_auth.get(reverse
                                            ('posts:post_detail',
                                             kwargs={'post_id': self.post.id}
                                             ))
        post_text_0 = {response.context['post'].text: 'Тестовый пост',
                       response.context['post'].group: self.group,
                       response.context['post'].author: self.author.username}
        for value, expected in post_text_0.items():
            self.assertEqual(post_text_0[value], expected)
        self.assertEqual(response.context['count_post'], 1)
        self.assertEqual(self.post.id, 1)

    def test_create_post_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом."""
        response = self.authorized_auth.get(reverse('posts:create_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_added_correctly(self):
        """Пост при создании добавлен корректно"""
        post = Post.objects.create(
            text='Текст поста',
            author=self.author,
            group=self.group)
        response_index = self.authorized_auth.get(
            reverse('posts:index'))
        response_group = self.authorized_auth.get(
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}))
        response_profile = self.authorized_auth.get(
            reverse('posts:profile',
                    kwargs={'username': f'{self.author.username}'}))
        index = response_index.context['page_obj']
        group = response_group.context['page_obj']
        profile = response_profile.context['page_obj']
        self.assertIn(post, index, 'ошибка на главной странице')
        self.assertIn(post, group, 'ошибка в группе')
        self.assertIn(post, profile, 'ошибка в профиле')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Описание',
            slug='test-slug',
        )
        cls.posts = []
        for i in range(NUMB_OF_POSTS):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.author,
                group=cls.group,
            )
            )
        Post.objects.bulk_create(cls.posts)

        cls.guest_client = Client()
        cls.authorized_auth = Client()
        cls.authorized_auth.force_login(cls.author)

    def test_first_page_contains_ten_posts(self):
        urls_list = {
            reverse('posts:index'): 'index',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'group',
            reverse('posts:profile',
                    kwargs={'username': self.author}): 'profile',
        }
        for tested_url in urls_list.keys():
            response = self.authorized_auth.get(tested_url)
            self.assertEqual(
                len(response.context['page_obj']), TEMP_NUMB_FIRST_PAGE
            )

    def test_second_page_contains_three_posts(self):
        urls_list = {
            reverse('posts:index') + '?page=2': 'index',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2': 'group',
            reverse('posts:profile',
                    kwargs={'username': self.author}) + '?page=2': 'profile',
        }
        for tested_url in urls_list.keys():
            response = self.authorized_auth.get(tested_url)
            self.assertEqual(
                len(response.context['page_obj']), TEMP_NUMB_SECOND_PAGE
            )
