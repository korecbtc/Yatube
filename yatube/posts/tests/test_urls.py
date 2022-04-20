from http import HTTPStatus

from django.test import Client, TestCase

from posts.models import Group, Post, User

ANY_POST_ID = 44


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Author_Ivan')
        cls.group = Group.objects.create(
            title='Persik',
            slug='persik',
            description='Opisanie',
        )
        cls.post = Post.objects.create(
            text='Test_text',
            author=cls.user,
            group=cls.group,
            pk=ANY_POST_ID
        )
        cls.templates_url_names = {
            '/': 'posts/index.html',
            ('/group/' + cls.group.slug + '/'): 'posts/group_list.html',
            ('/profile/' + str(cls.user) + '/'): 'posts/profile.html',
            ('/posts/' + str(ANY_POST_ID) + '/'): 'posts/post_detail.html',
        }

    def setUp(self):
        self.no_author = User.objects.create_user(username='No_Author_Ivan')
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(self.no_author)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response_auth_no_author = self.authorized_client_no_author.get(
                    address)
                response_auth_author = self.authorized_client_author.get(
                    address)
                response_auth_guest = self.client.get(
                    address)
                self.assertTemplateUsed(
                    response_auth_no_author,
                    template, 'Шаблон не соответствует запросу')
                self.assertTemplateUsed(
                    response_auth_author,
                    template, 'Шаблон не соответствует запросу')
                self.assertTemplateUsed(
                    response_auth_guest,
                    template, 'Шаблон не соответствует запросу')

    def test_edit_url_uses_correct_template(self):
        """Страница /posts/<post_id>/edit/ использует правильный шаблон"""

        """Авторизованный пользователь, но не автор"""
        response_auth_no_author = self.authorized_client_no_author.get(
            '/posts/' + str(ANY_POST_ID) + '/edit/')
        self.assertRedirects(
            response_auth_no_author, '/posts/' + str(ANY_POST_ID) + '/')

        """Авторизованный пользователь - автор"""
        response_auth_author = self.authorized_client_author.get(
            '/posts/' + str(ANY_POST_ID) + '/edit/')
        self.assertTemplateUsed(
            response_auth_author,
            'posts/create_post.html', 'Шаблон не соответствует запросу')

        """Гость"""
        response_guest = self.client.get(
            '/posts/' + str(ANY_POST_ID) + '/edit/')
        self.assertRedirects(
            response_guest,
            '/auth/login/?next=/posts/' + str(ANY_POST_ID) + '/edit/')

    def test_create_url_uses_correct_template(self):
        """Страница /create/ использует правильный шаблон"""

        """Авторизованный пользователь, но не автор"""
        response_auth_no_author = self.authorized_client_no_author.get(
            '/create/')
        self.assertTemplateUsed(
            response_auth_no_author,
            'posts/create_post.html', 'Шаблон не соответствует запросу')

        """Авторизованный пользователь - автор"""
        response_auth_author = self.authorized_client_author.get('/create/')
        self.assertTemplateUsed(
            response_auth_author, 'posts/create_post.html',
            'Шаблон не соответствует запросу')

        """Гость"""
        response_guest = self.client.get('/create/')
        self.assertRedirects(response_guest, '/auth/login/?next=/create/')

    def test_wrong_uri_returns_404(self):
        """Несуществующая страница возвращает кастомную 404"""
        response = self.client.get('/none/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_commments_needs_login(self):
        """Только авторизированный пользователь может писать комментарии"""
        response_guest = self.client.get(
            '/posts/' + str(ANY_POST_ID) + '/comment/'
        )
        self.assertRedirects(
            response_guest, '/auth/login/?next=/posts/44/comment/'
        )
        response_auth_no_author = self.authorized_client_no_author.get(
            '/posts/' + str(ANY_POST_ID) + '/comment/'
        )
        self.assertRedirects(
            response_auth_no_author,
            '/posts/' + str(ANY_POST_ID) + '/'
        )
        response_auth_author = self.authorized_client_author.get(
            '/posts/' + str(ANY_POST_ID) + '/comment/'
        )
        self.assertRedirects(
            response_auth_author,
            '/posts/' + str(ANY_POST_ID) + '/'
        )
