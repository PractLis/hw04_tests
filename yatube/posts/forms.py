from django.contrib.auth import get_user_model
from django.forms import ModelForm

from .models import Comment, Post
from .models import Post

User = get_user_model()

class PostForm(ModelForm):
    class Meta():
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Выбор группы',
            'image': 'Картинка',
        }
        help_texts = {
            'text': 'Обязательное поле',
            'group': 'Необязательное поле',
            'image': 'Загрузите картинку',
        }

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст комментария.'
        }
        help_texts = {
            'text': 'Напишите сюда текст комментария.'
        }