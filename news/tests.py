from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from news.models import Article, Category, EditorialSettings, WireStory

User = get_user_model()


class NewsroomWorkflowTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='India', slug='india', order=1)
        self.superuser = User.objects.create_superuser(
            email='boss@example.com',
            password='s3cretpass!',
        )
        self.staff = User.objects.create_user(
            email='writer@example.com',
            password='s3cretpass!',
            is_staff=True,
        )
        self.reader = User.objects.create_user(
            email='reader@example.com',
            password='s3cretpass!',
        )

    def _make_article(self, author, status=Article.STATUS_DRAFT, **kwargs):
        defaults = {
            'title': 'A staff story',
            'body': '<p>Hello</p>',
            'category': self.category,
            'author': author,
            'status': status,
        }
        defaults.update(kwargs)
        return Article.objects.create(**defaults)

    def test_reader_cannot_open_newsroom(self):
        self.client.force_login(self.reader)
        response = self.client.get(reverse('news:newsroom_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_staff_submit_goes_to_review(self):
        self.client.force_login(self.staff)
        article = self._make_article(self.staff)
        self.client.post(reverse('news:newsroom_submit', args=[article.pk]))
        article.refresh_from_db()
        self.assertEqual(article.status, Article.STATUS_REVIEW)

    def test_auto_approve_publishes_immediately(self):
        settings_obj = EditorialSettings.load()
        settings_obj.auto_approve_staff = True
        settings_obj.save()
        self.client.force_login(self.staff)
        article = self._make_article(self.staff)
        self.client.post(reverse('news:newsroom_submit', args=[article.pk]))
        article.refresh_from_db()
        self.assertEqual(article.status, Article.STATUS_PUBLISHED)

    def test_superuser_can_approve_and_pin(self):
        article = self._make_article(self.staff, status=Article.STATUS_REVIEW)
        other = self._make_article(
            self.staff,
            status=Article.STATUS_PUBLISHED,
            title='Older pin',
            is_featured=True,
            published_at=timezone.now() - timedelta(days=1),
        )
        self.client.force_login(self.superuser)
        self.client.post(reverse('news:newsroom_publish', args=[article.pk]))
        article.refresh_from_db()
        self.assertEqual(article.status, Article.STATUS_PUBLISHED)
        self.client.post(reverse('news:newsroom_pin', args=[article.pk]))
        article.refresh_from_db()
        other.refresh_from_db()
        self.assertTrue(article.is_featured)
        self.assertFalse(other.is_featured)

    def test_superuser_can_grant_staff(self):
        self.client.force_login(self.superuser)
        self.client.post(reverse('news:newsroom_toggle_staff', args=[self.reader.pk]))
        self.reader.refresh_from_db()
        self.assertTrue(self.reader.is_staff)

    def test_homepage_uses_pinned_hero(self):
        newest = self._make_article(
            self.staff,
            status=Article.STATUS_PUBLISHED,
            title='Newest',
            published_at=timezone.now(),
        )
        pinned = self._make_article(
            self.staff,
            status=Article.STATUS_PUBLISHED,
            title='Pinned hero',
            is_featured=True,
            published_at=timezone.now() - timedelta(days=2),
        )
        self.client.force_login(self.reader)
        response = self.client.get(reverse('news:home'))
        self.assertEqual(response.context['lead'], pinned)
        self.assertNotEqual(response.context['lead'], newest)


class WireStoryPreviewTests(TestCase):
    def test_wire_story_opens_on_the_news_outlet_first(self):
        story = WireStory.objects.create(
            title='A live wire headline',
            source_url='https://example.com/original-report',
            source_name='Example News',
            excerpt='A short GNews-provided preview.',
        )

        response = self.client.get(story.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, story.title)
        self.assertContains(response, 'Read original report')
        self.assertContains(response, story.source_url)
