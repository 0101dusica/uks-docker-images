from django.test import TestCase
from django.db import IntegrityError
from users.models import User
from repositories.models import Repository, Star


class RepositoryModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='owner', email='owner@example.com', password='pass1234'
        )

    def test_create_repository(self):
        repo = Repository.objects.create(
            name='myrepo', owner=self.user, visibility='public'
        )
        self.assertEqual(repo.name, 'myrepo')
        self.assertEqual(repo.owner, self.user)
        self.assertEqual(repo.visibility, 'public')
        self.assertFalse(repo.is_official)
        self.assertEqual(repo.stars, 0)

    def test_str_representation(self):
        repo = Repository.objects.create(name='myrepo', owner=self.user)
        self.assertEqual(str(repo), 'owner/myrepo')

    def test_unique_name_per_owner(self):
        Repository.objects.create(name='myrepo', owner=self.user)
        with self.assertRaises(IntegrityError):
            Repository.objects.create(name='myrepo', owner=self.user)

    def test_same_name_different_owners(self):
        other_user = User.objects.create_user(
            username='other', email='other@example.com', password='pass1234'
        )
        Repository.objects.create(name='myrepo', owner=self.user)
        repo2 = Repository.objects.create(name='myrepo', owner=other_user)
        self.assertEqual(repo2.name, 'myrepo')

    def test_default_visibility_is_public(self):
        repo = Repository.objects.create(name='myrepo', owner=self.user)
        self.assertEqual(repo.visibility, 'public')

    def test_private_repository(self):
        repo = Repository.objects.create(
            name='secret', owner=self.user, visibility='private'
        )
        self.assertEqual(repo.visibility, 'private')

    def test_delete_user_cascades_to_repositories(self):
        Repository.objects.create(name='repo1', owner=self.user)
        Repository.objects.create(name='repo2', owner=self.user)
        self.assertEqual(Repository.objects.count(), 2)
        self.user.delete()
        self.assertEqual(Repository.objects.count(), 0)


class StarModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='staruser', email='star@example.com', password='pass1234'
        )
        self.owner = User.objects.create_user(
            username='owner', email='owner@example.com', password='pass1234'
        )
        self.repo = Repository.objects.create(
            name='popular', owner=self.owner, visibility='public'
        )

    def test_create_star(self):
        star = Star.objects.create(user=self.user, repository=self.repo)
        self.assertEqual(star.user, self.user)
        self.assertEqual(star.repository, self.repo)

    def test_unique_star_per_user_repo(self):
        Star.objects.create(user=self.user, repository=self.repo)
        with self.assertRaises(IntegrityError):
            Star.objects.create(user=self.user, repository=self.repo)

    def test_str_representation(self):
        star = Star.objects.create(user=self.user, repository=self.repo)
        self.assertEqual(str(star), 'staruser -> popular')

    def test_delete_repo_cascades_to_stars(self):
        Star.objects.create(user=self.user, repository=self.repo)
        self.assertEqual(Star.objects.count(), 1)
        self.repo.delete()
        self.assertEqual(Star.objects.count(), 0)
