from django.test import TestCase

from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Просто описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост' * 10,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_title_label(self):
        """verbose_name поля title совпадает с ожидаемым."""
        group = PostModelTest.group
        # Получаем из свойста класса Task значение verbose_name для title
        verbose = group._meta.get_field('title').verbose_name
        self.assertEqual(verbose, 'Группа')

    def test_title_help_text(self):
        """help_text поля title совпадает с ожидаемым."""
        post = PostModelTest.group
        # Получаем из свойста класса Task значение help_text для title
        help_text = post._meta.get_field('title').help_text
        self.assertEqual(help_text, 'Группа, к которой будет относиться пост')
