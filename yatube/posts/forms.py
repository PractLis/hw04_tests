from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    class Meta():
        model = Post
        fields = ('text', 'group')
        labels = {
            'text': 'Текст поста',
            'group': 'Выбор группы',
        }
        help_texts = {
            'text': 'Обязательное поле',
            'group': 'Необязательное поле',
        }
