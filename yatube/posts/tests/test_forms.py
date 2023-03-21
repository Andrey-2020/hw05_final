import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post, User

AUTHOR_USERNAME = 'HasNoName'
USER_USERNAME = 'TestUser'
GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'test-slug'
GROUP_DESCRIPTION = 'Тестовое описание'
POST_TEXT = 'Тестовый пост'

INDEX_URL = reverse('posts:index')
GROUP_LIST_URL = reverse('posts:group_list', args=[GROUP_SLUG])
PROFILE_URL = reverse('posts:profile', args=[AUTHOR_USERNAME])
POST_CREATE_URL = reverse('posts:post_create')
FORM_FIELD_TEXT_HELP_TEXT = 'Текст публикации'
FORM_FIELD_GROUP_HELP_TEXT = ('Пожалуйста, '
                              'выберете наиболее подходящую группу из списка '
                              'или оставьте без группы')

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.form = PostForm()
        cls.formComment = CommentForm()
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
        )
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
        cls.POST_DETAIL_URL = reverse('posts:post_detail', kwargs={
            'post_id': cls.post.pk})
        cls.POST_EDIT_URL = reverse('posts:post_edit', kwargs={
            'post_id': cls.post.pk})
        cls.POST_ADD_COMMENT = reverse('posts:add_comment', kwargs={
            'post_id': cls.post.pk})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskCreateFormTests.user)

    def test_form_help_text(self):
        """Проверка поля help_text"""
        text_help_text = TaskCreateFormTests.form.fields['text'].help_text
        group_help_text = TaskCreateFormTests.form.fields['group'].help_text
        self.assertEquals(text_help_text, FORM_FIELD_TEXT_HELP_TEXT)
        self.assertEquals(group_help_text, FORM_FIELD_GROUP_HELP_TEXT)

    def test_create_task(self):
        """Валидная форма создает запись с картинкой в Post."""
        tasks_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=TaskCreateFormTests.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'author': TaskCreateFormTests.user,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, PROFILE_URL)

        self.assertEqual(Post.objects.count(), tasks_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=TaskCreateFormTests.user,
                image='posts/small.gif',
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма изменяет запись в Post."""
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'Измененный текст',
            'group': TaskCreateFormTests.group.id,
        }
        response = self.authorized_client.post(
            TaskCreateFormTests.POST_EDIT_URL,
            follow=True,
            data=form_data
        )
        self.assertEqual(Post.objects.count(), tasks_count)

        self.assertRedirects(response, TaskCreateFormTests.POST_DETAIL_URL)

        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=TaskCreateFormTests.user,
                group=TaskCreateFormTests.group.id,
            ).exists()
        )

    def test_comment_form(self):
        """Проверяем добавление комментария."""
        tasks_count = Comment.objects.count()
        form_data = {
            'text': 'текст поста',
        }
        response = self.authorized_client.post(
            TaskCreateFormTests.POST_ADD_COMMENT,
            data=form_data
        )
        self.assertEqual(Comment.objects.count(), tasks_count + 1)

        self.assertRedirects(response, TaskCreateFormTests.POST_DETAIL_URL)

        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                author=TaskCreateFormTests.user,
            ).exists()
        )

    def test_redirect(self):
        """Проверяем, что корректно работает автоматическое перенаправление."""
        response = self.guest_client.get(
            TaskCreateFormTests.POST_EDIT_URL,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        redirect_url = (
            reverse('users:login') + '?next='
            + TaskCreateFormTests.POST_EDIT_URL
        )
        self.assertRedirects(response, redirect_url)
