from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

NUMBER_OF_POSTS = 10


def paginator_func(post_list, request):
    paginator = Paginator(post_list, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    post_list = Post.objects.all()
    page_obj = paginator_func(post_list, request)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = paginator_func(post_list, request)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all()
    page_obj = paginator_func(post_list, request)
    following = False
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=user
    ).exists()
    context = {
        'user_obj': user,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'form': form,
        'comments': comments,
        'post': post
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    user = request.user
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        text = form.cleaned_data['text']
        group = form.cleaned_data['group']
        author = user
        post = Post.objects.create(
            text=text,
            group=group,
            author=author,
            image=form.cleaned_data['image']
        )

        post.save()

        return redirect('posts:profile', user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    user = request.user
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if post.author != user:
        return redirect('posts:post_detail', post_id)
    if not form.is_valid():
        context = {
            'form': form,
            'is_edit': is_edit,
            'post_id': post.pk
        }
        return render(request, 'posts/create_post.html', context)
    post.text = form.cleaned_data['text']
    post.group = form.cleaned_data['group']
    post.author = user
    post.save()
    return redirect('posts:post_detail', post_id)


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
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator_func(post_list, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    if request.user.username != username:
        user_obj = get_object_or_404(User, username=username)
        if not Follow.objects.filter(
            user=request.user,
            author=user_obj
        ).exists():
            user_obj = get_object_or_404(User, username=username)
            follow = Follow.objects.create(
                user=request.user,
                author=user_obj
            )
            follow.save()
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    if request.user.username != username:
        user_obj = get_object_or_404(User, username=username)
        unfollow = Follow.objects.filter(author=user_obj)
        unfollow.delete()
    return redirect('posts:follow_index')
