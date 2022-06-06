from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import paging


def index(request):
    template = 'posts/index.html'
    page_obj = paging(Post.objects.select_related(), request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group_recived = get_object_or_404(Group, slug=slug)
    page_obj = paging(group_recived.posts.all(), request)
    context = {
        'group': group_recived,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    post_user = get_object_or_404(User, username=username)
    if request.user.is_authenticated:
        follower = get_object_or_404(User, username=request.user)
    else:
        follower = None
    if post_user != follower:
        button_follow_visible = True
    else:
        button_follow_visible = False
    following = Follow.objects.filter(user=follower, author=post_user).exists()
    page_obj = paging(post_user.posts.all(), request)
    context = {
        'post_user': post_user,
        'page_obj': page_obj,
        'following': following,
        'visible': button_follow_visible
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post_detailed = get_object_or_404(
        Post.objects.select_related(), pk=post_id
    )
    comments = post_detailed.comments.all()
    form = CommentForm(request.POST or None)
    context = {
        'post': post_detailed,
        'comments': comments,
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:profile', request.user)
    return render(request, template, {'form': form, 'is_edit': False})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.pk)
    return render(
        request,
        template,
        {'form': form, 'is_edit': True, 'id': post_id}
    )


@login_required
def add_comment(request, post_id):
    post: Post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    followers: Follow = Follow.objects.filter(user=request.user)
    follow_list = User.objects.filter(following__in=followers)
    page_obj = paging(Post.objects.filter(author__in=follow_list), request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    follower = get_object_or_404(User, username=request.user)
    following = get_object_or_404(User, username=username)
    if not Follow.objects.filter(user=follower, author=following).exists():
        if follower != following:
            Follow.objects.create(
                user=follower,
                author=following
            )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    follower = get_object_or_404(User, username=request.user)
    following = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(
        user=follower,
        author=following
    )
    if len(follow) == 1:
        follow.delete()
    return redirect('posts:profile', username)
