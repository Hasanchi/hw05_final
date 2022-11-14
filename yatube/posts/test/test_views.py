from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Post, Group

User = get_user_model()


class PostPagesTests(TestCase):
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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
            image=uploaded
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def accordance_field_context(self, response):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_page_show_correct_context(self):
        """post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.accordance_field_context(response)

    def test_post_edit_page_show_correct_context(self):
        """post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            )
        )
        self.accordance_field_context(response)

    def test_pages_show_correct_context(self):
        context = {
            reverse('posts:index'): self.post,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): self.post,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ): self.post,
        }
        for reverse_page, object in context.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                page_object = response.context['page_obj'][0]
                self.assertEqual(page_object.text, object.text)
                self.assertEqual(page_object.author, object.author)
                self.assertEqual(page_object.group, object.group)
                self.assertEqual(page_object.image, object.image)

    def test_post_detail_page_show_correct_context(self):
        """post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(response.context['posts'].id, self.post.id)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='posts_author',
        )
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        post_all = 13
        posts = (
            Post(
                text=f'Test {value}',
                author=cls.user,
                group=cls.group
            ) for value in range(post_all)
        )
        Post.objects.bulk_create(list(posts))

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        context = {
            reverse('posts:index'): 'page_obj',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): 'page_obj',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ): 'page_obj',
        }
        for revers_name, objects in context.items():
            with self.subTest(revers_name=revers_name):
                response = self.authorized_client.get(revers_name)
                self.assertEqual(len(response.context[objects]), 10)

    def test_second_page_contains_three_records(self):
        context = {
            reverse('posts:index'): 'page_obj',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): 'page_obj',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ): 'page_obj',
        }
        for revers_name, objects in context.items():
            with self.subTest(revers_name=revers_name):
                response = self.authorized_client.get(revers_name, {'page': 2})
                self.assertEqual(len(response.context[objects]), 3)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='posts_author',
        )
        cls.follower = User.objects.create(
            username='follower',
        )
        cls.not_follower = User.objects.create(
            username='not_follower',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Рандомный текст статьи',
        )

    def setUp(self):
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        self.not_follower_client = Client()
        self.not_follower_client.force_login(self.follower)
        self.guest_client = Client()

    def test_following(self):
        """Тест на отображение постов в follow_index не подписчика автора"""
        response = self.not_follower_client.get(reverse('posts:follow_index'))
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj), 0)

    def test_following_and_unfollowing(self):
        """Проверка на возможность подписать и отписаться"""
        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username}
            )
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj), 1)
        self.follower_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author.username}
            )
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj), 0)

    def test_redirect_guest_client(self):
        response = self.guest_client.get('/profile/posts_author/follow/')
        self.assertRedirects(
            response,
            '/auth/login/?next=/profile/posts_author/follow/'
        )


class CacheIndexPageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='posts_author',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        content = self.authorized_client.get(reverse('posts:index')).content
        Post.objects.create(
            text='Пост 1',
            author=self.user,
        )
        content_1 = self.authorized_client.get(reverse('posts:index')).content
        self.assertEqual(content, content_1)
        cache.clear()
        content_2 = self.authorized_client.get(reverse('posts:index')).content
        self.assertNotEqual(content_1, content_2)
