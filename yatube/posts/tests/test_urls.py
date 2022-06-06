from http import HTTPStatus

from django.test import Client, TestCase

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_user = User.objects.create_user(username='PostAuthor')
        cls.auth_user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Просто описание'
        )

    def setUp(self) -> None:
        super().setUp()
        self.auth_client = Client()
        self.post_client = Client()
        self.auth_client.force_login(self.auth_user)
        self.post_client.force_login(self.post_user)
        self.post = Post.objects.create(
            author=self.post_user,
            text='Тестовый пост' * 10,
        )

    def test_post_pages_for_any_user(self):
        post_pages = {
            '/': 'posts/index.html',
            '/group/test-group/': 'posts/group_list.html',
            '/profile/NoName/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
        }
        for field, expected_value in post_pages.items():
            with self.subTest(field=field):
                response = self.client.get(field)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, expected_value)

    def test_post_pages_for_auth_user(self):
        response = self.client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.auth_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.post_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_post_pages_for_post_user(self):
        response = self.client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.auth_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.post_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_post_pages_for_unexisting_page(self):
        response = self.auth_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_follow_index_page(self):
        response = self.client.get('/follow/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, '/auth/login/?next=/follow/')
        response = self.auth_client.get('/follow/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'posts/follow.html')
