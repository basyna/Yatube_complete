
import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestPost(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = User.objects.create_user(username='NoName')
        cls.follow_user = User.objects.create_user(username='Follow')
        cls.no_follow_user = User.objects.create_user(username='NoFollow')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Просто описание'
        )
        cls.empty_group = Group.objects.create(
            title='Пустая группа',
            slug='empty-group',
            description='Описание: это пустая группа'
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        super().setUp()
        self.auth_client = Client()
        self.auth_client.force_login(self.auth_user)
        self.test_post: Post = Post.objects.create(
            author=self.auth_user,
            text='Тестовый пост' * 10,
            group=self.group,
            image=self.uploaded
        )
        self.comment: Comment = Comment.objects.create(
            post=self.test_post,
            author=self.auth_user,
            text='Тестовый коммент'
        )

    def test_posts_templates(self):
        reverse_data = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_list', args=(self.group.slug,)):
                'posts/group_list.html',
            reverse('posts:profile', args=(self.auth_user.username,)):
                'posts/profile.html',
            reverse('posts:post_detail', args=(self.test_post.pk,)):
                'posts/post_detail.html',
            reverse('posts:post_create'):
                'posts/create_post.html',
            reverse('posts:post_edit', args=(self.test_post.pk,)):
                'posts/create_post.html'
        }
        for name, expected in reverse_data.items():
            with self.subTest(name=name):
                response = self.auth_client.get(name)
                self.assertTemplateUsed(response, expected)

    def post_checking(self, post: Post) -> None:
        self.assertEqual(post.author, self.auth_user)
        self.assertEqual(post.text, self.test_post.text)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image, self.test_post.image)

    def test_post_context_index(self):
        response = self.client.get(reverse('posts:index'))
        post: Post = response.context['page_obj'].object_list[0]
        self.post_checking(post)

    def test_cache_index(self):
        response = self.client.get(reverse('posts:index'))
        content = response.content
        post: Post = response.context['page_obj'].object_list[0]
        post.delete()
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(response.content, content)
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, content)

    def test_post_context_group(self):
        response = self.client.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        post: Post = response.context['page_obj'].object_list[0]
        self.post_checking(post)

    def test_post_context_profile(self):
        response = self.client.get(
            reverse('posts:profile', args=(self.auth_user.username,))
        )
        post: Post = response.context['page_obj'].object_list[0]
        self.post_checking(post)

    def test_post_context_detail(self):
        response = self.client.get(
            reverse('posts:post_detail', args=(self.test_post.pk,))
        )
        post: Post = response.context['post']
        self.post_checking(post)
        self.assertEqual(
            response.context['comments'].first().text,
            self.comment.text
        )

    def test_posts_not_in_empty_group(self):
        response = self.client.get(
            reverse('posts:group_list', args=(self.empty_group.slug,))
        )
        self.assertNotIn(
            self.test_post, response.context['page_obj'].object_list)

    def test_form_post_create_content(self):
        response = self.auth_client.get(reverse('posts:post_create'))
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertEqual(response.context['is_edit'], False)

    def test_form_post_edit_content(self):
        response = self.auth_client.get(
            reverse('posts:post_edit', args=(self.test_post.pk,))
        )
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertEqual(response.context['is_edit'], True)

    def test_follow(self):
        response = self.client.get(
            reverse('posts:profile_follow', args=(self.follow_user.username,))
        )
        self.assertRedirects(
            response,
            '/auth/login/?next=/profile/Follow/follow/'
        )
        response = self.auth_client.get(
            reverse('posts:profile_follow', args=(self.follow_user.username,))
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', args=(self.follow_user.username,))
        )
        self.assertTrue(Follow.objects.filter(
            user=self.auth_user, author=self.follow_user).exists())

    def test_unfollow(self):
        Follow.objects.create(
            user=self.auth_user,
            author=self.follow_user
        )
        response = self.client.get(
            reverse(
                'posts:profile_unfollow',
                args=(self.follow_user.username,)
            )
        )
        self.assertRedirects(
            response,
            '/auth/login/?next=/profile/Follow/unfollow/'
        )
        response = self.auth_client.get(
            reverse(
                'posts:profile_unfollow',
                args=(self.follow_user.username,)
            )
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', args=(self.follow_user.username,))
        )
        self.assertFalse(Follow.objects.filter(
            user=self.auth_user, author=self.follow_user).exists())

    def test_follow_post_appearance(self):
        Follow.objects.create(
            user=self.auth_user,
            author=self.follow_user
        )
        self.follow_post: Post = Post.objects.create(
            author=self.follow_user,
            text='Тестовый пост для подписчика',
            group=self.group,
            image=self.uploaded
        )
        response = self.auth_client.get(
            reverse('posts:follow_index'))
        self.assertIn(
            self.follow_post, response.context['page_obj'].object_list)
        """Создаём клиента для неподписанного пользователя."""
        self.no_follow_client = Client()
        self.no_follow_client.force_login(self.no_follow_user)
        response = self.no_follow_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(
            self.follow_post, response.context['page_obj'].object_list)


class TestPostPaginator(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.EXTRA_PAGES = 3
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Просто описание'
        )

    def setUp(self) -> None:
        super().setUp()
        self.auth_client = Client()
        self.auth_user = User.objects.create_user(username='NoName')
        self.auth_client.force_login(self.auth_user)
        for i in range(settings.POSTS_ON_PAGE + self.EXTRA_PAGES):
            Post.objects.create(
                author=self.auth_user,
                text='Тестовый пост ' + str(i),
                group=self.group
            )

    def test_posts_paging(self):
        reverse_data = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-group'}),
            reverse('posts:profile', args=(self.auth_user,)),
        }
        pages = [
            {
                'number': 1,
                'count': settings.POSTS_ON_PAGE,
            },
            {
                'number': 2,
                'count': self.EXTRA_PAGES,
            }
        ]
        for pages_set in reverse_data:
            with self.subTest(pages_set=pages_set):
                for page_info in pages:
                    response = self.auth_client.get(
                        pages_set,
                        {'page': page_info['number']}
                    )
                    page: Page = response.context['page_obj']
                    self.assertEqual(len(page.object_list), page_info['count'])
