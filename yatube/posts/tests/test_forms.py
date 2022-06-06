import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestPost(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Просто описание'
        )
        cls.second_group = Group.objects.create(
            title='Вторая тестовая группа',
            slug='second-group',
            description='Просто описание второй группы'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.form = PostForm()
        cls.comment_form = CommentForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        super().setUp()
        self.auth_client = Client()
        self.auth_client.force_login(self.auth_user)
        Post.objects.create(
            author=self.auth_user,
            group=self.group,
            text='Первый тестовый пост'
        )

    def test_post_create(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
            'image': self.uploaded
        }
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', args=(self.auth_user.username,))
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post: Post = Post.objects.first()
        self.assertEqual(post.author, self.auth_user)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.image, 'posts/small.gif')

    def test_post_unautorized_create(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            '/auth/login/?next=/create/'
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_post_edit(self):
        post: Post = Post.objects.first()
        form_data = {
            'text': 'Новый тестовый текст',
            'group': self.second_group.pk,
        }
        response = self.auth_client.post(
            reverse('posts:post_edit', args=(post.pk,)),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=(post.pk,))
        )
        post: Post = Post.objects.first()
        self.assertEqual(post.author, self.auth_user)
        self.assertEqual(post.group, self.second_group)
        self.assertEqual(post.text, form_data['text'])

    def test_post_unautorized_edit(self):
        post: Post = Post.objects.first()
        form_data = {
            'text': 'Новый тестовый текст',
            'group': self.second_group.pk,
        }
        response = self.client.post(
            reverse('posts:post_edit', args=(post.pk,)),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            '/auth/login/?next=/posts/1/edit/'
        )

    def test_comment_creation(self):
        post = Post.objects.first()
        comments_count = post.comments.count()
        form_data = {
            'text': 'Тестовый комментарий'
        }
        response = self.auth_client.post(
            reverse('posts:add_comment', args=(post.pk,)),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=(post.pk,))
        )
        self.assertEqual(post.comments.count(), comments_count + 1)
        self.assertEqual(post.comments.first().text, form_data['text'])

    def test_comment_unauthorized_creation(self):
        post = Post.objects.first()
        form_data = {
            'text': 'Тестовый комментарий'
        }
        response = self.client.post(
            reverse('posts:add_comment', args=(post.pk,)),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            '/auth/login/?next=%2Fposts%2F1%2Fcomment%2F'
        )
