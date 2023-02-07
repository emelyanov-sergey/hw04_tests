from http import HTTPStatus
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Теcтовое описание',
        )
        cls.post = Post.objects.create(
            author=PostFormTests.user,
            text='Тестовый текст',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_create_post(self):
        """Проверка создания поста"""
        posts_count = Post.objects.count()
        form_data = {'text': 'Тестовый текст'}
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True,)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text='Тестовый текст').exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit(self):
        """Валидная форма изменяет запись поста для авторизованного"""
        posts_count = Post.objects.count()
        form_data = {'text': 'Изменяем текст', 'group': self.group.id}
        response = self.authorized_client.post(reverse(
            'posts:post_edit',
            args=({self.post.id})
        ), data=form_data, follow=True,)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(text='Изменяем текст').exists)
        self.assertEqual(response.status_code, HTTPStatus.OK)
