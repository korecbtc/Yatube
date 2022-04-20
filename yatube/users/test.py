from django.test import TestCase
from django.urls import reverse

from posts.models import User


class AuthTestForm(TestCase):
    def test_signup(self):
        """Регистрация создает нового пользователя"""
        form_data = {
            'username': 'Papandopulo',
            'password1': 'Q89utYr4)ss',
            'password2': 'Q89utYr4)ss'
        }
        count_of_posts = User.objects.count()
        response = self.client.post(
            reverse('users:signup'), data=form_data, follow=True)
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), count_of_posts + 1)
