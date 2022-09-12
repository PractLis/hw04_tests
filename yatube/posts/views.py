from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.shortcuts import render


from .forms import PostForm
from .models import Group, Post, User
from .utils import get_page_context


User = get_user_model()


def index(request):
    template: str = 'posts/index.html'
    context = get_page_context(Post.objects.all(), request)
    return render(request, template, context)


def group_posts(request, slug):
    template: str = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        'group': group,
        'posts': posts,
    }
    context.update(get_page_context(posts, request))
    return render(request, template, context)


def profile(request, username):
    template: str = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_count = author.posts.count()
    profile_list = author.posts.select_related('author', 'group')
    context = {
        'author': author,
        'post_count': post_count,
    }
    context.update(get_page_context(profile_list, request))
    return render(request, template, context)


def post_detail(request, post_id):
    template: str = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    count_post = post.author.posts.count()
    context = {
        'post': post,
        'count_post': count_post,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template: str = 'posts/create_post.html'
    form = PostForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        post_form = form.save(commit=False)
        post_form.author = request.user
        post_form.save()
        return redirect('posts:profile', username=request.user)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(request.POST or None, instance=post)
    if request.method == 'POST' and form.is_valid():
        form = form.save(commit=False)
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, template, {'form': form, 'is_edit': True})
