from django.test import TestCase, Client
from django.urls import reverse
from django import forms

from posts.models import Post, Group, User


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='NoName')
        cls.user2 = User.objects.create(username='second')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=PostPagesTests.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
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
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.group)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        first_object = response.context['page_obj'][0]
        form_fields = {
            first_object.text: self.post.text,
            first_object.group: self.group,
            first_object.author: self.user
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_text_0 = {
            response.context['post'].text: self.post.text,
            response.context['post'].group: self.group,
            response.context['post'].author: self.user.username
        }
        for value, expected in post_text_0.items():
            self.assertEqual(post_text_0[value], expected)

    def test_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_check_post_on_homepage_correct(self):
        """Созданный пост корректно отображается на Главной странице """
        post = Post.objects.create(
            text=self.post.text,
            author=self.user,
            group=self.group
        )
        response_index = self.authorized_client.get(reverse('posts:index'))
        response_group = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        response_profile = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        index = response_index.context['page_obj']
        group = response_group.context['page_obj']
        profile = response_profile.context['page_obj']
        self.assertIn(post, index, 'Поста нет на главной')
        self.assertIn(post, group, 'Поста нет в группе')
        self.assertIn(post, profile, 'Поста нет в профиле')

    def test_post_added_correctly_user2(self):
        """Пост при создании не добавляется другому пользователю
           Но виден на главной и в группе"""
        group2 = Group.objects.create(title='Тестовая группа 2',
                                      slug='test_group2')
        posts_count = Post.objects.filter(group=self.group).count()
        post = Post.objects.create(
            text='Тестовый пост от другого автора',
            author=self.user2,
            group=group2
        )
        response_profile = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username}))
        group = Post.objects.filter(group=self.group).count()
        profile = response_profile.context['page_obj']
        self.assertEqual(group, posts_count, 'поста нет в другой группе')
        self.assertNotIn(post, profile,
                         'поста нет в группе другого пользователя')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )
        for i in range(1, 14):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group
            )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create(username='Auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PaginatorViewsTest.post.author)

    def test_homepage_first_page_contains_ten_records(self):
        '''Проверка: количество постов на первой странице Главной равно 10.'''
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_homepage_second_page_contains_three_records(self):
        '''Проверка: количество постов на второй странице Главной равно 3.'''
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_group_page_first_page_contains_ten_records(self):
        '''Проверка: количество постов на первой странице Группы равно 10.'''
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_page_second_page_contains_three_records(self):
        '''Проверка: количество постов на второй странице Группы равно 3.'''
        response = self.client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_profile_page_first_page_contains_ten_records(self):
        '''Проверка: количество постов на первой странице Профиля равно 10.'''
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}
            )
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_page_second_page_contains_three_records(self):
        '''Проверка: количество постов на второй странице Профиля равно 3.'''
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}
            ) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
