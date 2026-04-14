from django.test import TestCase, Client
from django.urls import reverse
from users.models import User
from repositories.models import Repository, Star


class RepositoryCRUDTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='owner', email='owner@example.com', password='pass1234'
        )
        self.client.login(username='owner', password='pass1234')

    def test_my_repositories_page_loads(self):
        response = self.client.get(reverse('my-repositories'))
        self.assertEqual(response.status_code, 200)

    def test_create_repository_page_loads(self):
        response = self.client.get(reverse('create-repository'))
        self.assertEqual(response.status_code, 200)

    def test_create_repository(self):
        response = self.client.post(reverse('create-repository'), {
            'name': 'newrepo',
            'description': 'A test repo',
            'visibility': 'public',
        })
        self.assertRedirects(response, reverse('my-repositories'))
        self.assertTrue(Repository.objects.filter(name='newrepo', owner=self.user).exists())

    def test_create_duplicate_repository(self):
        Repository.objects.create(name='existing', owner=self.user)
        response = self.client.post(reverse('create-repository'), {
            'name': 'existing',
            'description': 'duplicate',
            'visibility': 'public',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Repository.objects.filter(name='existing').count(), 1)

    def test_edit_repository(self):
        repo = Repository.objects.create(
            name='myrepo', owner=self.user, description='old', visibility='public'
        )
        response = self.client.post(reverse('edit-repository', args=[repo.id]), {
            'description': 'updated description',
            'visibility': 'private',
        })
        self.assertRedirects(response, reverse('my-repositories'))
        repo.refresh_from_db()
        self.assertEqual(repo.description, 'updated description')
        self.assertEqual(repo.visibility, 'private')

    def test_cannot_edit_other_users_repository(self):
        other = User.objects.create_user(
            username='other', email='other@example.com', password='pass1234'
        )
        repo = Repository.objects.create(name='notmine', owner=other)
        response = self.client.get(reverse('edit-repository', args=[repo.id]))
        self.assertEqual(response.status_code, 403)

    def test_delete_repository(self):
        repo = Repository.objects.create(name='todelete', owner=self.user)
        response = self.client.post(reverse('delete-repository', args=[repo.id]))
        self.assertRedirects(response, reverse('my-repositories'))
        self.assertFalse(Repository.objects.filter(id=repo.id).exists())

    def test_cannot_delete_other_users_repository(self):
        other = User.objects.create_user(
            username='other', email='other@example.com', password='pass1234'
        )
        repo = Repository.objects.create(name='notmine', owner=other)
        response = self.client.post(reverse('delete-repository', args=[repo.id]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Repository.objects.filter(id=repo.id).exists())

    def test_unauthenticated_cannot_create_repository(self):
        self.client.logout()
        response = self.client.get(reverse('create-repository'))
        self.assertEqual(response.status_code, 302)


class PublicRepositoriesTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='owner', email='owner@example.com', password='pass1234'
        )

    def test_public_repos_page_loads(self):
        response = self.client.get(reverse('public-repositories'))
        self.assertEqual(response.status_code, 200)

    def test_only_public_repos_shown(self):
        Repository.objects.create(
            name='public1', owner=self.user, visibility='public'
        )
        Repository.objects.create(
            name='private1', owner=self.user, visibility='private'
        )
        response = self.client.get(reverse('public-repositories'))
        self.assertContains(response, 'public1')
        self.assertNotContains(response, 'private1')

    def test_public_repos_api(self):
        Repository.objects.create(
            name='apirepo', owner=self.user, visibility='public'
        )
        response = self.client.get('/api/repositories/public/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(response.json()['results'][0]['name'], 'apirepo')

    def test_search_by_name(self):
        Repository.objects.create(name='django-app', owner=self.user, visibility='public')
        Repository.objects.create(name='flask-app', owner=self.user, visibility='public')
        response = self.client.get(reverse('public-repositories') + '?search=django')
        self.assertContains(response, 'django-app')
        self.assertNotContains(response, 'flask-app')

    def test_search_by_description(self):
        Repository.objects.create(
            name='repo1', owner=self.user, visibility='public',
            description='A machine learning project'
        )
        Repository.objects.create(
            name='repo2', owner=self.user, visibility='public',
            description='A web framework'
        )
        response = self.client.get(reverse('public-repositories') + '?search=machine')
        self.assertContains(response, 'repo1')
        self.assertNotContains(response, 'repo2')

    def test_sort_by_stars(self):
        Repository.objects.create(name='unpopular', owner=self.user, visibility='public', stars=1)
        Repository.objects.create(name='popular', owner=self.user, visibility='public', stars=100)
        response = self.client.get(reverse('public-repositories') + '?sort=stars')
        content = response.content.decode()
        self.assertTrue(content.index('popular') < content.index('unpopular'))

    def test_sort_by_name(self):
        Repository.objects.create(name='zebra', owner=self.user, visibility='public')
        Repository.objects.create(name='alpha', owner=self.user, visibility='public')
        response = self.client.get(reverse('public-repositories') + '?sort=name')
        content = response.content.decode()
        self.assertTrue(content.index('alpha') < content.index('zebra'))

    def test_filter_by_official(self):
        Repository.objects.create(name='official-repo', owner=self.user, visibility='public', is_official=True)
        Repository.objects.create(name='normal-repo', owner=self.user, visibility='public', is_official=False)
        response = self.client.get(reverse('public-repositories') + '?badge=official')
        self.assertContains(response, 'official-repo')
        self.assertNotContains(response, 'normal-repo')

    def test_filter_by_verified_publisher(self):
        verified_user = User.objects.create_user(
            username='verified', email='verified@example.com',
            password='pass1234', badge='verified_publisher'
        )
        Repository.objects.create(name='verified-repo', owner=verified_user, visibility='public')
        Repository.objects.create(name='normal-repo', owner=self.user, visibility='public')
        response = self.client.get(reverse('public-repositories') + '?badge=verified_publisher')
        self.assertContains(response, 'verified-repo')
        self.assertNotContains(response, 'normal-repo')

    def test_api_search(self):
        Repository.objects.create(name='django-app', owner=self.user, visibility='public')
        Repository.objects.create(name='flask-app', owner=self.user, visibility='public')
        response = self.client.get('/api/repositories/public/?search=django')
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(response.json()['results'][0]['name'], 'django-app')

    def test_api_filter_by_badge(self):
        Repository.objects.create(name='official', owner=self.user, visibility='public', is_official=True)
        Repository.objects.create(name='normal', owner=self.user, visibility='public')
        response = self.client.get('/api/repositories/public/?badge=official')
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(response.json()['results'][0]['name'], 'official')


class StarTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username='owner', email='owner@example.com', password='pass1234'
        )
        self.user = User.objects.create_user(
            username='staruser', email='star@example.com', password='pass1234'
        )
        self.repo = Repository.objects.create(
            name='starrable', owner=self.owner, visibility='public'
        )
        self.client.login(username='staruser', password='pass1234')

    def test_star_repository(self):
        response = self.client.post(reverse('toggle-star', args=[self.repo.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Star.objects.filter(user=self.user, repository=self.repo).exists())
        self.repo.refresh_from_db()
        self.assertEqual(self.repo.stars, 1)

    def test_unstar_repository(self):
        Star.objects.create(user=self.user, repository=self.repo)
        self.repo.stars = 1
        self.repo.save()
        response = self.client.post(reverse('toggle-star', args=[self.repo.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Star.objects.filter(user=self.user, repository=self.repo).exists())
        self.repo.refresh_from_db()
        self.assertEqual(self.repo.stars, 0)

    def test_unauthenticated_cannot_star(self):
        self.client.logout()
        response = self.client.post(reverse('toggle-star', args=[self.repo.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Star.objects.filter(repository=self.repo).exists())
