from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse

from users.models import User


LOGGER = 'repositories.views'


class RegistryCatalogLoggingTests(TestCase):
    def setUp(self):
        self.client = Client()

    @patch('repositories.views.RegistryService')
    def test_successful_catalog_fetch_logs_info(self, mock_registry_class):
        mock_registry_class.return_value.get_catalog.return_value = ['repo1', 'repo2']
        with self.assertLogs(LOGGER, level='INFO') as cm:
            self.client.get(reverse('registry-catalog'))
        self.assertTrue(any('Registry catalog fetched' in msg for msg in cm.output))

    @patch('repositories.views.RegistryService')
    def test_successful_catalog_fetch_log_contains_count(self, mock_registry_class):
        mock_registry_class.return_value.get_catalog.return_value = ['repo1', 'repo2']
        with self.assertLogs(LOGGER, level='INFO') as cm:
            self.client.get(reverse('registry-catalog'))
        catalog_log = next(msg for msg in cm.output if 'Registry catalog fetched' in msg)
        self.assertIn('2', catalog_log)

    @patch('repositories.views.RegistryService')
    def test_failed_catalog_fetch_logs_error(self, mock_registry_class):
        mock_registry_class.return_value.get_catalog.return_value = None
        with self.assertLogs(LOGGER, level='ERROR') as cm:
            self.client.get(reverse('registry-catalog'))
        self.assertTrue(any('Failed to fetch registry catalog' in msg for msg in cm.output))

    @patch('repositories.views.RegistryService')
    def test_empty_catalog_logs_info_with_zero_count(self, mock_registry_class):
        mock_registry_class.return_value.get_catalog.return_value = []
        with self.assertLogs(LOGGER, level='INFO') as cm:
            self.client.get(reverse('registry-catalog'))
        self.assertTrue(any('Registry catalog fetched' in msg for msg in cm.output))


class RegistryTagsLoggingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass1234',
        )

    @patch('repositories.views.RegistryService')
    def test_successful_tags_fetch_logs_info(self, mock_registry_class):
        mock_instance = mock_registry_class.return_value
        mock_instance.get_tags.return_value = ['latest', 'v1.0']
        mock_instance.get_manifest.return_value = {'digest': 'sha256:abc', 'size': 100}
        with self.assertLogs(LOGGER, level='INFO') as cm:
            self.client.get(reverse('registry-tags', args=['owner/myrepo']))
        self.assertTrue(any('Registry tags fetched' in msg for msg in cm.output))

    @patch('repositories.views.RegistryService')
    def test_successful_tags_fetch_log_contains_repo_name_and_count(self, mock_registry_class):
        mock_instance = mock_registry_class.return_value
        mock_instance.get_tags.return_value = ['latest', 'v1.0']
        mock_instance.get_manifest.return_value = {'digest': 'sha256:abc', 'size': 100}
        with self.assertLogs(LOGGER, level='INFO') as cm:
            self.client.get(reverse('registry-tags', args=['owner/myrepo']))
        tags_log = next(msg for msg in cm.output if 'Registry tags fetched' in msg)
        self.assertIn('owner/myrepo', tags_log)
        self.assertIn('2', tags_log)

    @patch('repositories.views.RegistryService')
    def test_failed_tags_fetch_logs_error(self, mock_registry_class):
        mock_registry_class.return_value.get_tags.return_value = None
        with self.assertLogs(LOGGER, level='ERROR') as cm:
            self.client.get(reverse('registry-tags', args=['owner/myrepo']))
        self.assertTrue(any('Failed to fetch registry tags' in msg for msg in cm.output))

    @patch('repositories.views.RegistryService')
    def test_failed_tags_fetch_log_contains_repo_name(self, mock_registry_class):
        mock_registry_class.return_value.get_tags.return_value = None
        with self.assertLogs(LOGGER, level='ERROR') as cm:
            self.client.get(reverse('registry-tags', args=['owner/myrepo']))
        error_log = next(msg for msg in cm.output if 'Failed to fetch registry tags' in msg)
        self.assertIn('owner/myrepo', error_log)
