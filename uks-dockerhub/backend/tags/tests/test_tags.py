from django.test import TestCase, Client
from django.db import IntegrityError
from django.urls import reverse
from users.models import User
from repositories.models import Repository
from tags.models import Tag


class TagModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='owner', email='owner@example.com', password='pass1234'
        )
        self.repo = Repository.objects.create(
            name='myrepo', owner=self.user
        )

    def test_create_tag(self):
        tag = Tag.objects.create(name='v1.0', repository=self.repo)
        self.assertEqual(tag.name, 'v1.0')
        self.assertEqual(tag.repository, self.repo)

    def test_str_representation(self):
        tag = Tag.objects.create(name='latest', repository=self.repo)
        self.assertEqual(str(tag), 'myrepo:latest')

    def test_unique_tag_per_repo(self):
        Tag.objects.create(name='v1.0', repository=self.repo)
        with self.assertRaises(IntegrityError):
            Tag.objects.create(name='v1.0', repository=self.repo)

    def test_same_tag_name_different_repos(self):
        other_user = User.objects.create_user(
            username='other', email='other@example.com', password='pass1234'
        )
        other_repo = Repository.objects.create(name='otherrepo', owner=other_user)
        Tag.objects.create(name='latest', repository=self.repo)
        tag2 = Tag.objects.create(name='latest', repository=other_repo)
        self.assertEqual(tag2.name, 'latest')

    def test_delete_repo_cascades_to_tags(self):
        Tag.objects.create(name='v1.0', repository=self.repo)
        Tag.objects.create(name='v2.0', repository=self.repo)
        self.assertEqual(Tag.objects.count(), 2)
        self.repo.delete()
        self.assertEqual(Tag.objects.count(), 0)


class TagViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='owner', email='owner@example.com', password='pass1234'
        )
        self.repo = Repository.objects.create(
            name='myrepo', owner=self.user
        )
        self.client.login(username='owner', password='pass1234')

    def test_manage_tags_page_loads(self):
        response = self.client.get(reverse('manage-tags', args=[self.repo.id]))
        self.assertEqual(response.status_code, 200)

    def test_add_tag(self):
        response = self.client.post(reverse('manage-tags', args=[self.repo.id]), {
            'add_tag': '1',
            'tag_name': 'v1.0',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Tag.objects.filter(repository=self.repo, name='v1.0').exists())

    def test_add_empty_tag_name(self):
        response = self.client.post(reverse('manage-tags', args=[self.repo.id]), {
            'add_tag': '1',
            'tag_name': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cannot be empty')

    def test_add_duplicate_tag(self):
        Tag.objects.create(name='v1.0', repository=self.repo)
        response = self.client.post(reverse('manage-tags', args=[self.repo.id]), {
            'add_tag': '1',
            'tag_name': 'v1.0',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')

    def test_delete_tag(self):
        tag = Tag.objects.create(name='v1.0', repository=self.repo)
        response = self.client.post(
            reverse('delete-tag', args=[self.repo.id, tag.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())

    def test_cannot_manage_tags_on_other_users_repo(self):
        other = User.objects.create_user(
            username='other', email='other@example.com', password='pass1234'
        )
        other_repo = Repository.objects.create(name='notmine', owner=other)
        response = self.client.get(reverse('manage-tags', args=[other_repo.id]))
        self.assertEqual(response.status_code, 403)

    def test_cannot_delete_tag_on_other_users_repo(self):
        other = User.objects.create_user(
            username='other', email='other@example.com', password='pass1234'
        )
        other_repo = Repository.objects.create(name='notmine', owner=other)
        tag = Tag.objects.create(name='v1.0', repository=other_repo)
        response = self.client.post(
            reverse('delete-tag', args=[other_repo.id, tag.id])
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Tag.objects.filter(id=tag.id).exists())

    def test_unauthenticated_cannot_manage_tags(self):
        self.client.logout()
        response = self.client.get(reverse('manage-tags', args=[self.repo.id]))
        self.assertEqual(response.status_code, 302)
