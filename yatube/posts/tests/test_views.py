from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post, User

POSTS_PER_PAGE = 10


AUTHOR_USERNAME = 'HasNoName'
USER_USERNAME = 'USER'
USER_OTHER_USERNAME = 'USER_OTHER'
USER_USERNAME = 'TestUser'
GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'test-slug'
GROUP_DESCRIPTION = 'Тестовое описание'
POST_TEXT = 'Тестовый пост'

INDEX_URL = reverse('posts:index')
GROUP_LIST_URL = reverse('posts:group_list', args=[GROUP_SLUG])
PROFILE_URL = reverse('posts:profile', args=[AUTHOR_USERNAME])
POST_CREATE_URL = reverse('posts:post_create')
PAGE_NOT_FOUND = '/not_found/404'
FOLLOW_INDEX = reverse('posts:follow_index')
PROFILE_FOLLOW = reverse('posts:profile_follow', kwargs={
    'username': AUTHOR_USERNAME})
PROFILE_UNFOLLOW = reverse('posts:profile_unfollow', kwargs={
    'username': AUTHOR_USERNAME})


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.COUNT_OF_POSTS = 13
        cls.COUNT_ON_PAGE = 10
        cls.OTHERS_OF_POSTS = 3
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        Post.objects.bulk_create([
            Post(
                text=f'{POST_TEXT} {i}', author=cls.author, group=cls.group
            ) for i in range(cls.COUNT_OF_POSTS)
        ])

        cls.templates_pages_names = {
            INDEX_URL: 'posts/index.html',
            GROUP_LIST_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.author)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        for reverse_name in (PaginatorViewsTest.
                             templates_pages_names.keys()):
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    POSTS_PER_PAGE)

    def test_second_page_contains_three_records(self):
        for reverse_name in (PaginatorViewsTest.
                             templates_pages_names.keys()):
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 PaginatorViewsTest.OTHERS_OF_POSTS)


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.user_follower = User.objects.create_user(username=USER_USERNAME)
        cls.user_other_follower = User.objects.create_user(
            username=USER_OTHER_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
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
            author=cls.user,
            text=POST_TEXT,
            group=cls.group,
            image=cls.uploaded
        )

        cls.POST_DETAIL_URL = reverse('posts:post_detail', kwargs={
            'post_id': TaskPagesTests.post.pk})
        cls.POST_EDIT_URL = reverse('posts:post_edit', kwargs={
            'post_id': TaskPagesTests.post.pk})

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskPagesTests.user)
        self.authorized_client_user_follower = Client()
        self.authorized_client_user_follower.force_login(
            TaskPagesTests.user_follower
        )

        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            INDEX_URL: 'posts/index.html',
            GROUP_LIST_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            TaskPagesTests.POST_DETAIL_URL: 'posts/post_detail.html',
            POST_CREATE_URL: 'posts/create_post.html',
            TaskPagesTests.POST_EDIT_URL: 'posts/create_post.html',
            PAGE_NOT_FOUND: 'core/404.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(INDEX_URL)
        first_object = response.context['page_obj'][0]
        task_title_0 = first_object.author
        task_text_0 = first_object.text
        task_image_0 = first_object.image
        self.assertEqual(task_title_0, TaskPagesTests.user)
        self.assertEqual(task_text_0, POST_TEXT)
        self.assertEqual(task_image_0, Post.objects.all()[0].image)
        self.assertIn('small', task_image_0.name)

    def test_group_posts_pages_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(GROUP_LIST_URL))
        first_object = response.context['page_obj'][0]
        task_title_0 = first_object.author
        task_text_0 = first_object.text
        task_group_0 = first_object.group
        task_image_0 = first_object.image
        self.assertEqual(task_title_0, TaskPagesTests.user)
        self.assertEqual(task_text_0, POST_TEXT)
        self.assertEqual(task_group_0.slug, GROUP_SLUG)
        self.assertEqual(task_image_0, Post.objects.all()[0].image)
        self.assertIn('small', task_image_0.name)

    def test_profile_pages_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(PROFILE_URL))
        first_object = response.context['page_obj'][0]
        task_title_0 = first_object.author
        task_text_0 = first_object.text
        task_group_0 = first_object.group
        task_image_0 = first_object.image
        author = response.context['author']
        self.assertEqual(task_title_0, TaskPagesTests.user)
        self.assertEqual(task_text_0, POST_TEXT)
        self.assertEqual(task_group_0.slug, GROUP_SLUG)
        self.assertEqual(author, TaskPagesTests.user)
        self.assertEqual(task_image_0, Post.objects.all()[0].image)
        self.assertIn('small', task_image_0.name)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.
                    get(TaskPagesTests.POST_DETAIL_URL))
        self.assertEqual(response.context['post'].author, TaskPagesTests.user)
        self.assertEqual(response.context['post'].text, POST_TEXT)
        self.assertEqual(response.context['post'].image,
                         Post.objects.all()[0].image)
        self.assertIn('small', response.context['post'].image.name)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(POST_CREATE_URL)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        print(response.context.get('form').fields.get('image'))
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(TaskPagesTests.POST_EDIT_URL)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        is_edit = response.context.get('is_edit')
        self.assertTrue(is_edit)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_cache_context(self):
        """Тестирование кэша главной страницы работает исправно."""
        tasks_count = Post.objects.count()
        responses = {
            'guest_client': self.guest_client.get(INDEX_URL),
            'authorized_client': self.authorized_client.get(INDEX_URL),
        }
        form_data = {
            'text': POST_TEXT,
            'author': TaskPagesTests.user,
        }
        self.authorized_client.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True,
        )

        clients = {
            'guest_client': self.guest_client,
            'authorized_client': self.authorized_client,
        }
        for user, client in clients.items():
            with self.subTest(user=user):
                response = client.get(INDEX_URL)
                self.assertEqual(responses[user].content, response.content)
                self.assertEqual(Post.objects.count(), tasks_count + 1)
        cache.clear()
        for user, client in clients.items():
            with self.subTest(user=user):
                response = client.get(INDEX_URL)
                self.assertNotEqual(responses[user].content, response.content)

    def test_profile_follow_and_unfollow_context(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок"""
        tasks_count = Follow.objects.count()
        response_follow = self.authorized_client_user_follower.get(
            PROFILE_FOLLOW)
        self.assertEqual(Follow.objects.count(), tasks_count + 1)
        self.assertRedirects(response_follow, PROFILE_URL)
        response_unfollow = self.authorized_client_user_follower.get(
            PROFILE_UNFOLLOW)
        self.assertEqual(Follow.objects.count(), tasks_count)
        self.assertRedirects(response_unfollow, PROFILE_URL)
        tasks_count = Follow.objects.count()
        self.authorized_client.get(
            PROFILE_FOLLOW)
        self.assertEqual(Follow.objects.count(), tasks_count)

    def test_profile_follow_index_context(self):
        """Новая запись пользователя появляется в ленте тех,
          кто на него подписан и не появляется в ленте тех, кто не подписан."""
        authorized_client_user_2_follower = Client()
        authorized_client_user_2_follower.force_login(
            TaskPagesTests.user_other_follower
        )
        self.authorized_client_user_follower.get(PROFILE_FOLLOW)

        Post.objects.create(
            author=TaskPagesTests.user,
            text=POST_TEXT,
            group=TaskPagesTests.group,
            image=TaskPagesTests.uploaded
        )
        response_follow = self.authorized_client_user_follower.get(
            FOLLOW_INDEX)
        response_unfollow = authorized_client_user_2_follower.get(
            FOLLOW_INDEX)
        self.assertNotEqual(response_follow.content, response_unfollow.content)
