import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class YatubeTestForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Ivan')
        cls.authorized_user = Client()
        cls.authorized_user.force_login(cls.user)
        cls.post = Post.objects.create(
            text='New post',
            author=cls.user,
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
        cls.edited_small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.edited_uploaded = SimpleUploadedFile(
            name='edited_small.gif',
            content=cls.edited_small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_new_post(self):
        """Отправка формы создает новую запись"""
        form_data = {
            'text': 'Test_text',
            'image': self.uploaded
        }
        count_of_posts = Post.objects.count()
        response = self.authorized_user.post(
            reverse('posts:post_create'), data=form_data, follow=True)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), count_of_posts + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Test_text',
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        """Отправка формы изменяет запись"""
        form_data = {
            'text': 'Edited_text',
            'image': self.edited_uploaded,
        }
        count_of_posts = Post.objects.count()
        response = self.authorized_user.post(reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.pk}), data=form_data, follow=True)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}))
        """Не создается еще один пост, а изменяется текущий"""
        self.assertEqual(Post.objects.count(), count_of_posts)
        self.assertContains(response, 'Edited_text')
        self.assertTrue(
            Post.objects.filter(
                text='Edited_text',
                image='posts/edited_small.gif'
            ).exists()
        )

    def test_comment(self):
        """После успешной отправки комментарий появляется на странице поста"""
        form_data = {
            'text': 'Test_comment!'
        }
        response = self.authorized_user.post(reverse(
            'posts:add_comment', kwargs={'post_id': self.post.pk}
        ), data=form_data, follow=True)
        self.assertContains(response, 'Test_comment!')
