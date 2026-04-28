from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from repositories.models import Repository  

User = get_user_model()


class PublicRepositorySearchTest(TestCase):

    def setUp(self):
        
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass"
        )

        
        self.repo1 = Repository.objects.create(
            name="nginx",
            description="web server",
            visibility="public",
            is_official=True,
            stars=100,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            owner=self.user
        )

       
        self.repo2 = Repository.objects.create(
            name="redis",
            description="cache system",
            visibility="public",
            is_official=False,
            stars=50,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            owner=self.user
        )

       
        self.private_repo = Repository.objects.create(
            name="secret",
            description="hidden",
            visibility="private",
            is_official=False,
            stars=10,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            owner=self.user
        )

    def test_view_returns_only_public_repositories(self):
        response = self.client.get(reverse('public_repositories'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "nginx")
        self.assertContains(response, "redis")
        self.assertNotContains(response, "secret")

    def test_search_by_name(self):
        response = self.client.get(reverse('public_repositories'), {'q': 'nginx'})

        self.assertContains(response, "nginx")
        self.assertNotContains(response, "redis")

    def test_search_by_description(self):
        response = self.client.get(reverse('public_repositories'), {'q': 'cache'})

        self.assertContains(response, "redis")
        self.assertNotContains(response, "nginx")

    def test_search_no_results(self):
        response = self.client.get(reverse('public_repositories'), {'q': 'unknown'})

        self.assertNotContains(response, "nginx")
        self.assertNotContains(response, "redis")
        self.assertContains(response, "No public repositories found.")

    def test_empty_query_returns_all(self):
        response = self.client.get(reverse('public_repositories'), {'q': ''})

        self.assertContains(response, "nginx")
        self.assertContains(response, "redis")

    def test_ordering_by_stars_when_searching(self):
        response = self.client.get(reverse('public_repositories'), {'q': 'e'})

        repos = list(response.context['repositories'])

        self.assertGreaterEqual(repos[0].stars, repos[1].stars)