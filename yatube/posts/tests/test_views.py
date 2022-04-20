import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

COUNT_OF_POSTS_ON_SECOND_PAGE_MUST_BE = 3
POSTS_PER_PAGE_MUST_BE = 10
ANY_POST_ID = 44
COUNT_OF_POSTS_IN_GROUP_MUST_BE = 0
FIRST_OBJ_OF_PAGE = 0


def check_context(self, first_object):
    """Вспомогательная функция для проверки контекста"""
    self.assertEqual(first_object.text, self.post.text)
    self.assertEqual(first_object.author, self.post.author)
    self.assertEqual(first_object.group, self.post.group)
    self.assertEqual(first_object.pub_date, self.post.pub_date)
    self.assertEqual(first_object.image, self.post.image)


def check_paginator(self, in_get, const):
    """Вспомогательная функция для проверки пажинатора"""
    response = self.authorized_client.get(in_get)
    self.assertEqual(len(response.context['page_obj']), const)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class YatubePagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Author_Ivan')
        """Создаю автора, на которго будет подписан Юзер"""
        cls.blogger = User.objects.create_user(username='Tolik')
        """Создаю автора, который не будет подписан на блоггера"""
        cls.not_blogger = User.objects.create_user(username='Oleg')
        """Создаю пустую группу для проверки отсутсвия в ней постов"""
        cls.empty_group = Group.objects.create(
            title='Turtle',
            slug='turtle',
            description='Opisanie_turtle',
        )
        cls.group = Group.objects.create(
            title='Persik',
            slug='persik',
            description='Opisanie',
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
        cls.post = Post.objects.create(
            text='Test_text',
            author=cls.user,
            group=cls.group,
            pk=ANY_POST_ID,
            pub_date='11.09.1987',
            image=cls.uploaded
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_not_blogger = Client()
        self.authorized_not_blogger.force_login(self.not_blogger)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user}): 'posts/profile.html',
            (reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk})): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][FIRST_OBJ_OF_PAGE]
        check_context(self, first_object)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_posts', kwargs={'slug': self.group.slug}))
        first_object = response.context['page_obj'][FIRST_OBJ_OF_PAGE]
        check_context(self, first_object)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.post.author}))
        first_object = response.context['page_obj'][FIRST_OBJ_OF_PAGE]
        check_context(self, first_object)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}))
        first_object = response.context['post']
        check_context(self, first_object)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_empty_group_show_correct_context(self):
        """Отсутствие постов в пустой группе"""
        """Значит, пост не попал в группу, для которой не был предназначен"""
        check_paginator(self, reverse(
            'posts:group_posts', kwargs={'slug': self.empty_group.slug}),
            COUNT_OF_POSTS_IN_GROUP_MUST_BE)

    def test_follower_add_remove_author(self):
        """Юзер добавляет/удаляет интересных авторов"""
        count_before = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.blogger.username}
        ))
        count_after = Follow.objects.count()
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.blogger.username}
            )
        )
        count_after_unfollow = Follow.objects.count()
        self.assertEqual(count_before, count_after - 1)
        self.assertEqual(count_before, count_after_unfollow)

    def test_new_post_in_followers(self):
        """Новая запись видна у подписчиков и не видна у остальных"""
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.blogger.username})
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        count_before = len(response.context['page_obj'])
        Post.objects.create(
            text='Stupid_text',
            author=self.blogger
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        count_after = len(response.context['page_obj'])
        """Новая запись у блоггера не видна у неподписчика"""
        response = self.authorized_not_blogger.get(
            reverse('posts:follow_index')
        )
        count_after_not_follower = len(response.context['page_obj'])
        self.assertEqual(count_before, count_after - 1)
        self.assertEqual(count_before, count_after_not_follower)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Ivan')
        cls.post = Post.objects.create(
            text='Test_text',
            author=cls.user,
        )

    def test_cache(self):
        """Кэширование работает"""
        response_before = self.client.get(reverse('posts:index'))
        self.post.delete()
        response_after = self.client.get(reverse('posts:index'))
        self.assertEqual(response_before.content, response_after.content)
        cache.clear()
        response_after_clear = self.client.get(reverse('posts:index'))
        self.assertNotEqual(
            response_before.content, response_after_clear.content
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Ivan')
        cls.group = Group.objects.create(
            title='Yabloko',
            slug='yabloko',
        )
        cls.post = []

        for i in range(
            COUNT_OF_POSTS_ON_SECOND_PAGE_MUST_BE + POSTS_PER_PAGE_MUST_BE
        ):
            cls.post.append(Post.objects.create(
                text='Test_text',
                author=cls.user,
                group=cls.group,
            ))

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        check_paginator(self, reverse(
            'posts:index'), POSTS_PER_PAGE_MUST_BE)
        check_paginator(self, reverse(
            'posts:group_posts', kwargs={'slug': self.group.slug}),
            POSTS_PER_PAGE_MUST_BE)
        check_paginator(self, reverse(
            'posts:profile', kwargs={'username': self.user}),
            POSTS_PER_PAGE_MUST_BE)

    def test_second_page_contains_three_records(self):
        check_paginator(self, reverse(
            'posts:index') + '?page=2', COUNT_OF_POSTS_ON_SECOND_PAGE_MUST_BE)
        check_paginator(self, reverse(
            'posts:group_posts', kwargs={'slug': self.group.slug}) + '?page=2',
            COUNT_OF_POSTS_ON_SECOND_PAGE_MUST_BE)
        check_paginator(self, reverse(
            'posts:profile', kwargs={'username': self.user}) + '?page=2',
            COUNT_OF_POSTS_ON_SECOND_PAGE_MUST_BE)
