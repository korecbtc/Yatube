from django.test import TestCase

from ..models import Group, Post, User

NUMBER_OF_SYMBOLS = 15


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
            text='Тестовый пост длинной более пятнадцати символов',
        )

    def test_models_have_correct_object_names(self):
        """У моделей корректно работает __str__."""
        group = PostModelTest.group
        expected_object_name_group = group.title
        self.assertEqual(expected_object_name_group, str(group))
        post = PostModelTest.post
        expected_object_name_post = post.text[:NUMBER_OF_SYMBOLS]
        self.assertEqual(expected_object_name_post, str(post))
