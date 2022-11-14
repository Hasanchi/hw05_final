from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый поставввввава',
        )

    def test_models_have_correct_object_names(self):
        post = self.post
        group = self.group
        str_objects_names = {
            post.text[:15]: str(post),
            group.title: str(group),
        }
        for value, expected in str_objects_names.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)
