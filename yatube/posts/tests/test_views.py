import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()

NUMB_OF_POSTS = 13
TEMP_NUMB_FIRST_PAGE = 10
TEMP_NUMB_SECOND_PAGE = 3

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class GroupViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.auth_user = User.objects.create_user(username='auth_user')
        small_gif_1 = (            
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif_1,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Описание',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            pub_date='Дата публикации',
            image=cls.uploaded,
            group=cls.group,
        )

        cls.guest_client = Client()
        cls.authorized_auth = Client()
        cls.authorized_auth.force_login(cls.author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

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
        """Проверка передачи верного context из view """
        pages = {
            reverse('posts:index'): self.post,
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}): self.post,
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}): self.post,

        }

        for reverse_name, post in pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_auth.get(reverse_name)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.text, post.text)
                self.assertEqual(first_object.id, post.id)
                self.assertEqual(first_object.group, post.group)
                self.assertEqual(first_object.pub_date, post.pub_date)
                self.assertEqual(first_object.image, post.image)

    def test_group_pages_show_correct_context(self):
        """Шаблон Group список постов, отфильтрованных по группе."""
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
        """Paginator предоставляет ожидаемое количество постов
         на первую страницую."""
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
        """Paginator предоставляет ожидаемое количество постов
         на вторую страницую."""
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

class CacheViewsTest(TestCase):
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

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = CacheViewsTest.authorized_auth.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='Новый тестовый пост',
            author=CacheViewsTest.author,
        )
        response_old = CacheViewsTest.authorized_auth.get(
            reverse('posts:index')
        )
        old_posts = response_old.content
        self.assertEqual(
            old_posts,
            posts,
            'Не возвращает кэшированную страницу.'
        )
        cache.clear()
        response_new = CacheViewsTest.authorized_auth.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts, 'Нет сброса кэша.')

class CommentViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.auth_user = User.objects.create_user(username='auth_user')
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

    def test_add_comment_for_guest(self):
        """гость не может оставить комментарий"""
        response = self.guest_client.get(
            reverse(
                'posts:add_comment',
                kwargs={
                    'post_id': self.post.id
                }
            )
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            ('Неавторизированный пользователь'
             ' не может оставлять комментарий')
        )

    def test_comment_available(self):
        """Авторизованные пользователи могут комментировать"""
        post=CommentViewsTest.post
        client = self.authorized_auth
        response = client.get(
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': post.id
                }
            )
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            ('Авторизированный пользователь'
             ' должен иметь возможность'
             ' оставлять комментарий')
        )
        comments_count = Comment.objects.filter(
            post=post.id
        ).count()
        form_data = {
            'text': 'test_comment',
        }

        response = client.post(
            reverse('posts:post_detail',
                    kwargs={
                        'post_id': post.id
                    }
                    ),
            data=form_data,
            follow=True
        )
        comments = Post.objects.filter(
            id=post.id
        ).values_list('comments', flat=True)
        self.assertEqual(
            comments.count(),
            comments_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(Comment.objects.filter(
            text='test_comment').exists())

class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.follower = User.objects.create_user(username='follower')
        cls.unfollowr = User.objects.create_user(username='unfollowr')
                
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
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)
        cls.authorized_follower = Client()
        cls.authorized_follower.force_login(cls.follower)
        cls.authorized_unfollowr = Client()
        cls.authorized_unfollowr.force_login(cls.unfollowr)

    def test_follow(self):
        """Тест работы подписки на автора."""
        client = FollowViewsTest.authorized_unfollowr
        user = FollowViewsTest.unfollowr
        author = FollowViewsTest.author
        client.get(
            reverse(
                'posts:profile_follow',
                args=[author.username]
            )
        )
        follower = Follow.objects.filter(
            user=user,
            author=author
        ).exists()
        self.assertTrue(
            follower,
            'Не работает подписка на автора'
        )

    def test_unfollow(self):
        """Тест работы отписки от автора."""
        client = FollowViewsTest.authorized_unfollowr
        user = FollowViewsTest.unfollowr
        author = FollowViewsTest.author
        client.get(
            reverse(
                'posts:profile_unfollow',
                args=[author.username]
            ),

        )
        follower = Follow.objects.filter(
            user=user,
            author=author
        ).exists()
        self.assertFalse(
            follower,
            'Не работает отписка от автора'
        )

    def test_new_author_post_for_follower(self):
        """Новая запись  появляется в ленте тех, кто на него подписан"""
        client = FollowViewsTest.authorized_follower
        author = FollowViewsTest.author
        group = FollowViewsTest.group
        client.get(
            reverse(
                'posts:profile_follow',
                args=[author.username]
            )
        )
        response_old = client.get(
            reverse('posts:follow_index')
        )
        old_posts = response_old.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_old.context.get('page_obj').object_list),
            1,
        )
        self.assertIn(
            FollowViewsTest.post,
            old_posts,
        )
        new_post = Post.objects.create(
            text='test_new_post',
            group=group,
            author=author
        )
        cache.clear()
        response_new = client.get(
            reverse('posts:follow_index')
        )
        new_posts = response_new.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_new.context.get('page_obj').object_list),
            2,
        )
        self.assertIn(
            new_post,
            new_posts,
        )

    def test_new_author_post_for_unfollower(self):
        """Новая запись не появляется в ленте тех, кто не подписан"""
        client = FollowViewsTest.authorized_unfollowr
        author = FollowViewsTest.author
        group = FollowViewsTest.group
        response_old = client.get(
            reverse('posts:follow_index')
        )
        old_posts = response_old.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_old.context.get('page_obj').object_list),
            0,
        )
        self.assertNotIn(
            FollowViewsTest.post,
            old_posts,
        )
        new_post = Post.objects.create(
            text='test_new_post',
            group=group,
            author=author
        )
        cache.clear()
        response_new = client.get(
            reverse('posts:follow_index')
        )
        new_posts = response_new.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_new.context.get('page_obj').object_list),
            0,
        )
        self.assertNotIn(
            new_post,
            new_posts,
        )
