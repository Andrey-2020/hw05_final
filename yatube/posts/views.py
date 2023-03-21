# posts/views.py
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import (get_list_or_404, get_object_or_404, redirect,
                              render)

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import paginate_queryset


def index(request):
    post_list = Post.objects.all()

    page_obj = paginate_queryset(request, post_list)

    context = {
        'title': settings.TITLE_INDEX,
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):

    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = paginate_queryset(request, post_list)

    context = {
        'group': group,
        'page_obj': page_obj,

    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()

    page_obj = paginate_queryset(request, post_list)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author).exists()
    context = {
        'user': request.user,
        'author': author,
        'title': settings.TITLE_INDEX,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_list = post.author.posts.all()

    commentForm = CommentForm(request.POST or None)
    page_obj = paginate_queryset(request, post_list)
    is_edit = request.user == post.author

    context = {
        'post': post,
        'title': settings.TITLE_INDEX,
        'page_obj': page_obj,
        'is_edit': is_edit,
        'form': commentForm,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    postForm = PostForm(request.POST or None,
                        files=request.FILES or None,
                        )
    template = 'posts/create_post.html'
    if postForm.is_valid():
        text = postForm.cleaned_data['text']
        group = postForm.cleaned_data['group']
        image = postForm.cleaned_data['image']
        author = request.user
        result = Post(author=author, text=text, group=group, image=image)
        result.save()
        return redirect('posts:profile', author)
    return render(request, template, {'form': postForm})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not request.user == post.author:
        return redirect('posts:post_detail', post.author)

    postForm = PostForm(request.POST or None,
                        files=request.FILES or None,
                        instance=post
                        )
    template = 'posts/create_post.html'
    if postForm.is_valid():
        postForm.save()
        return redirect('posts:post_detail', post_id)

    return render(request, template, {'form': postForm, 'is_edit': True})

# posts/views.py


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    if Follow.objects.filter(
            user=request.user).exists() is False:
        context = {
            'title': settings.TITLE_FOLLOW_INDEX,
            'page_obj': [],
        }
        return render(request, 'posts/follow.html', context)

    follow_list = get_list_or_404(Follow, user=request.user)
    posts = []
    for follow in follow_list:
        posts += Post.objects.filter(author=follow.author)

    page_obj = paginate_queryset(request, posts)

    context = {
        'title': settings.TITLE_FOLLOW_INDEX,
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect('posts:profile', author)
    if Follow.objects.filter(
            user=request.user,
            author=author).exists():
        return redirect('posts:profile', author)
    Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, user=request.user, author=author)
    follow.delete()
    return redirect('posts:profile', author)
