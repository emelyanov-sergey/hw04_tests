from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post, Group, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Author')
        cls.not_author = User.objects.create(username='No_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=PostURLTests.user,
            text='Тестовый пост',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_url_exists_everyone(self):
        """Страницы доступны всем пользователям"""
        address_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        for address in address_url_names:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """Страницы используют корректные шаблоны"""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/rerr/': 'core/404.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_not_exist_404_page(self):
        """Несуществующая страница выдает ошибку 404"""
        response = self.guest_client.get('/not_exist/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_author_edit_post(self):
        """Автору поста доступна страница редактирования"""
        url = f'/posts/{PostURLTests.post.pk}/edit/'
        response = self.authorized_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_no_author_edit_post(self):
        """Не автору поста не доступна страница поста и
           он перенаправляется на страницу поста"""
        self.authorized_client.force_login(self.not_author)
        url = f'/posts/{PostURLTests.post.pk}/edit/'
        response = self.authorized_client.get(url)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostURLTests.post.pk}
            ),
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_guest_edit_post(self):
        """Гостю не доступно редактирование поста"""
        url = f'/posts/{PostURLTests.post.pk}/edit/'
        response = self.guest_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_guest_dont_create_page(self):
        """Гость не может создать пост"""
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_url_authorized_create_page(self):
        """Авторизованному доступна страница создания поста"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
