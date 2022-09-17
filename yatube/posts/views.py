from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.shortcuts import render

from .forms import CommentForm, PostForm
from .models import Group, Post, User, Follow
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
    following = request.user.is_authenticated and \
        Follow.objects.filter(
            user=request.user,
            author=author
        ).exists()
    post_count = author.posts.count()
    profile_list = author.posts.select_related('author', 'group')
    context = {
        'author': author,
        'post_count': post_count,
        'following': following,
    }
    context.update(get_page_context(profile_list, request))
    return render(request, template, context)



def post_detail(request, post_id):
    template: str = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    count_post = post.author.posts.count()
    comments = post.comments.all()
    context = {
        'author': post.author,
        'post': post,
        'count_post': count_post,
        'comments': comments,
        'form': form,
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
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
        )
    if request.method == 'POST' and form.is_valid():
        form = form.save(commit=False)
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, template, context)

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id,)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect(
            'posts:post_detail',
            post_id=post.id,
        )
    return render(
        request,       
        'includes/comments.html',
        {
            'form': form,
            'post': post,

        }
    )

@login_required
def follow_index(request):
    template = 'posts/follow.html'
    posts = Post.objects.filter(author__following__user=request.user)
    context = get_page_context(posts, request)
    return render(request, template, context)

@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect(
            'posts:profile',
            username=username
        )
    follower = Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    if follower is True:
        return redirect(
            'posts:profile',
        )
    Follow.objects.create(user=request.user, author=author)
    return redirect(
        'posts:profile',
        username=username
    )

@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    if is_follower.exists():
        is_follower.delete()
    return redirect('posts:profile', username=author)

