from http import HTTPStatus

from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.any_client = Client()

    def test_static_pages(self):
        static_pages = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for field, expected_value in static_pages.items():
            with self.subTest(field=field):
                response = self.any_client.get(field)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, expected_value)
