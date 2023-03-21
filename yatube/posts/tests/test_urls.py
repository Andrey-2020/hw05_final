# posts/tests/test_urls.py
from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post, User

AUTHOR_USERNAME = 'HasNoName'
USER_USERNAME = 'TestUser'
GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'test-slug'
GROUP_DESCRIPTION = 'Тестовое описание'
POST_TEXT = 'Тестовый пост'

INDEX_URL = '/'
GROUP_LIST_URL = '/group/test-slug/'
PROFILE_URL = '/profile/HasNoName/'
POST_CREATE_URL = '/create/'


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
        )

        cls.POST_DETAIL_URL = f'/posts/{TaskURLTests.post.pk}/'
        cls.POST_EDIT_URL = f'/posts/{TaskURLTests.post.pk}/edit/'
        cls.url = {
            INDEX_URL: 'posts/index.html',
            GROUP_LIST_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            cls.POST_DETAIL_URL: 'posts/post_detail.html',
            cls.POST_EDIT_URL: 'posts/create_post.html',
            POST_CREATE_URL: 'posts/create_post.html',
        }
        cls.url_guest_client = {
            INDEX_URL: 'posts/index.html',
            GROUP_LIST_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            cls.POST_DETAIL_URL: 'posts/post_detail.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskURLTests.user)
        cache.clear()

    def test_urls_uses_correct_template_and_url(self):
        """URL-адрес использует соответствующий шаблон и
         доступен авторизованному пользователю."""

        for address, template in TaskURLTests.url.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                print(response)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_at_desired_location(self):
        """Страница доступна любому пользователю."""

        for address in TaskURLTests.url_guest_client.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
