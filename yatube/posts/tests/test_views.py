from django.test import TestCase, Client
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.cache import cache

from posts.models import Post, Group, User, Comment

POSTS_PER_PAGE = settings.POSTS_PER_PAGE


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
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=PostPagesTests.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Тестовый комментарий',
            author=cls.user,
        )

    def setUp(self):
        cache.clear()
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
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        first_object = response.context['page_obj'][0]
        data_fields = {
            first_object.text: self.post.text,
            first_object.group: self.group,
            first_object.author: self.user,
            first_object.image: self.post.image,
        }
        for value, expected in data_fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
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
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_added_correctly_user2(self):
        """Пост при создании не добавляется другому пользователю
           Но виден на главной и в группе"""
        post = Post.objects.create(
            text='Тестовый пост от другого автора',
            author=self.user2,
            group=self.group2
        )
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username}))
        self.assertNotIn(post, response.context['page_obj'],
                         'поста нет в группе другого пользователя')
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group2.slug})
        )
        context = response.context['page_obj'].object_list
        self.assertNotIn(self.post, context, 'поста нет в другой группе')

    def test_add_comment_on_post(self):
        """Комментарий появляется на странице поста"""
        comment_count = Comment.objects.count()
        form_data = {'text': self.comment.text}
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertContains(response, self.comment.text)
        self.assertEqual(Comment.objects.count(), comment_count + 1)

    def test_add_comment_only_authorized_client(self):
        comment_count = Comment.objects.count()
        form_data = {'text': self.comment.text}
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertTrue(Comment.objects.filter(
            text='Тестовый комментарий'
        ).exists())
        self.assertEqual(Comment.objects.count(), comment_count)

    def test_index_cache(self):
        response = self.authorized_client.get(reverse('posts:index'))
        Post.objects.create(
            text='Тестовый пост',
            author=self.user
        )
        response_2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, response_3.content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.POST_PER_SECOND_PAGE = 3
        cls.ALL_POSTS = POSTS_PER_PAGE + (cls.POST_PER_SECOND_PAGE)
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )
        for i in range(cls.ALL_POSTS):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group
            )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create(username='Auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PaginatorViewsTest.post.author)

    def test_homepage_first_page_contains_ten_records(self):
        '''Проверка: количество постов на первой странице Главной.'''
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), POSTS_PER_PAGE)

    def test_homepage_second_page_contains_three_records(self):
        '''Проверка: количество постов на второй странице Главной.'''
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         self.POST_PER_SECOND_PAGE)

    def test_group_page_first_page_contains_ten_records(self):
        '''Проверка: количество постов на первой странице Группы.'''
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(len(response.context['page_obj']), POSTS_PER_PAGE)

    def test_group_page_second_page_contains_three_records(self):
        '''Проверка: количество постов на второй странице Группы.'''
        response = self.client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ) + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         self.POST_PER_SECOND_PAGE)

    def test_profile_page_first_page_contains_ten_records(self):
        '''Проверка: количество постов на первой странице Профиля.'''
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}
            )
        )
        self.assertEqual(len(response.context['page_obj']), POSTS_PER_PAGE)

    def test_profile_page_second_page_contains_three_records(self):
        '''Проверка: количество постов на второй странице Профиля.'''
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}
            ) + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         self.POST_PER_SECOND_PAGE)
