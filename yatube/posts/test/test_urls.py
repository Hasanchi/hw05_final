from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Post, Group

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='post_author'
        )
        cls.user_2 = User.objects.create_user(
            username='another_user'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.post_author = Client()
        self.post_author.force_login(self.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_2)

    def test_urls_uses_autorized_client(self):
        """Проверка статус кода для авторезированного пользователя"""
        templates_authorized_client = {
            '/': 200,
            '/group/test_slug/': 200,
            '/profile/post_author/': 200,
            '/posts/1/': 200,
            '/posts/1/edit/': 302,
            '/create/': 200,
            '/unexisting_page/': 404,
        }
        templates_post_author = {
            '/': 200,
            '/group/test_slug/': 200,
            '/profile/post_author/': 200,
            '/posts/1/': 200,
            '/posts/1/edit/': 200,
            '/create/': 200,
            '/unexisting_page/': 404,
        }
        templates_no_autorized_client = {
            '/': 200,
            '/group/test_slug/': 200,
            '/profile/post_author/': 200,
            '/posts/1/': 200,
            '/posts/1/edit/': 302,
            '/create/': 302,
            '/unexisting_page/': 404,
        }
        client_dict = {
            self.guest_client: templates_no_autorized_client,
            self.authorized_client: templates_authorized_client,
            self.post_author: templates_post_author,
        }
        for client, template in client_dict.items():
            for url, response_code in template.items():
                with self.subTest(url=url):
                    status_code = client.get(url).status_code
                    self.assertEqual(status_code, response_code)

    def test_task_list_url_uses_correct_template(self):
        """Проверка соответствия адреса и шаблона"""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/post_author/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                adress_url = self.post_author.get(adress)
                self.assertTemplateUsed(adress_url, template)

    def test_guest_client_redirect(self):
        """Проверка на редирект НЕ авторизованного пользователя"""
        redirect_response = {
            '/create/': '/auth/login/?next=/create/',
            '/posts/1/edit/': '/auth/login/?next=/posts/1/edit/',
        }
        for url, redirect in redirect_response.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, redirect)

    def test_autorized_client_redirect(self):
        """Проверка на редирект НЕ авторизованного пользователя"""
        redirect_response = {
            '/posts/1/edit/': '/posts/1/',
        }
        for url, redirect in redirect_response.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertRedirects(response, redirect)
