import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        small_gif = (            
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small_old.gif',
            content=small_gif,
            content_type='image/gif'
        )

        small_gif_new = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded_new = SimpleUploadedFile(
            name='small_new.gif',
            content=small_gif_new,
            content_type='image/gif'
        )

        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Тестовое описание'
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            pub_date='Дата публикации',
            image=cls.uploaded,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)    

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_correct_create_post(self):
        """Проверка создания нового поста авторизованным пользователем."""
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'image': self.uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:profile', 
                                                kwargs={'username':
                                                self.author.username}))
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.id,
                text='Тестовый пост',
                image='posts/small_old.gif',
            ).exists()
        )


    def test_correct_edit_post(self):
        """Проверка редактирования поста авторизованным пользователем."""
        form_data = {
            'text': 'Тестовый текс',
            'group': self.group.id,
            'image': self.uploaded,
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
            'group': self.group.id,
            'image': self.uploaded_new,
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
        self.assertEqual(changed_post.image, 'posts/small_new.gif')

    def test_guest_create_post(self):
        """Проверка создания нового поста гостем."""
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Тестовый текс',
            'group': self.group.id,
            'image': self.uploaded
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

    def test_create_comment(self):
        """Проверка формы создания нового комментария."""
        author = self.author
        post = self.post
        client = self.authorized_client
        comments_count = Comment.objects.filter(
            post=post.id
        ).count()
        form_data = {
            'comment': 'test_comment',
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
        self.assertTrue(
            response,
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': post.id,
                }
            )
        )
        self.assertEqual(
            comments.count(),
            comments_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(Comment.objects.filter(
            text='test_comment').exists())

