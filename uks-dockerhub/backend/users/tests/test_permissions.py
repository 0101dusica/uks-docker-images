from django.test import TestCase, Client
from django.urls import reverse
from users.models import User


class AdminPermissionTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='regular', email='user@example.com',
            password='pass1234', role='user'
        )
        self.admin = User.objects.create_user(
            username='admin1', email='admin@example.com',
            password='pass1234', role='admin'
        )

    def test_admin_can_access_dashboard(self):
        self.client.login(username='admin1', password='pass1234')
        response = self.client.get(reverse('admin-dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_regular_user_cannot_access_admin_dashboard(self):
        self.client.login(username='regular', password='pass1234')
        response = self.client.get(reverse('admin-dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_access_admin_dashboard(self):
        response = self.client.get(reverse('admin-dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_view_user_details(self):
        self.client.login(username='admin1', password='pass1234')
        response = self.client.get(
            reverse('user-details', args=[self.user.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'username': 'regular',
            'first_name': '',
            'last_name': '',
            'email': 'user@example.com',
            'status': 'Active',
        })

    def test_admin_can_block_user(self):
        self.client.login(username='admin1', password='pass1234')
        response = self.client.post(
            reverse('block-user', args=[self.user.id])
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_user_details_not_found(self):
        self.client.login(username='admin1', password='pass1234')
        response = self.client.get(reverse('user-details', args=[9999]))
        self.assertEqual(response.status_code, 404)


class SuperadminPermissionTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='regular', email='user@example.com',
            password='pass1234', role='user'
        )
        self.admin = User.objects.create_user(
            username='admin1', email='admin@example.com',
            password='pass1234', role='admin'
        )
        self.superadmin = User.objects.create_user(
            username='super1', email='super@example.com',
            password='pass1234', role='superadmin'
        )

    def test_superadmin_can_access_dashboard(self):
        self.client.login(username='super1', password='pass1234')
        response = self.client.get(reverse('superadmin-dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_admin_cannot_access_superadmin_dashboard(self):
        self.client.login(username='admin1', password='pass1234')
        response = self.client.get(reverse('superadmin-dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_superadmin_can_create_admin(self):
        self.client.login(username='super1', password='pass1234')
        response = self.client.post(reverse('superadmin-dashboard'), {
            'add_admin': '1',
            'username': 'newadmin',
            'email': 'newadmin@example.com',
            'first_name': 'New',
            'last_name': 'Admin',
            'password1': 'AdminPass123!',
            'password2': 'AdminPass123!',
        })
        self.assertEqual(response.status_code, 302)
        new_admin = User.objects.get(username='newadmin')
        self.assertEqual(new_admin.role, 'admin')

    def test_superadmin_can_block_admin(self):
        self.client.login(username='super1', password='pass1234')
        response = self.client.post(
            reverse('superadmin-admin-block', args=[self.admin.id])
        )
        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertFalse(self.admin.is_active)

    def test_superadmin_can_view_user_details(self):
        self.client.login(username='super1', password='pass1234')
        response = self.client.get(
            reverse('superadmin-user-details', args=[self.user.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_superadmin_can_block_user(self):
        self.client.login(username='super1', password='pass1234')
        response = self.client.post(
            reverse('superadmin-user-block', args=[self.user.id])
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
