from django.test import TestCase
from users.models import User


class UserModelTests(TestCase):

    def test_create_user_with_default_role(self):
        user = User.objects.create_user(
            username='testuser', email='test@example.com', password='pass1234'
        )
        self.assertEqual(user.role, 'user')
        self.assertFalse(user.must_change_password)
        self.assertTrue(user.is_active)

    def test_create_admin_user(self):
        admin = User.objects.create_user(
            username='admin1', email='admin@example.com',
            password='pass1234', role='admin'
        )
        self.assertEqual(admin.role, 'admin')

    def test_create_superadmin_user(self):
        superadmin = User.objects.create_user(
            username='super1', email='super@example.com',
            password='pass1234', role='superadmin'
        )
        self.assertEqual(superadmin.role, 'superadmin')

    def test_email_must_be_unique(self):
        User.objects.create_user(
            username='user1', email='same@example.com', password='pass1234'
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='user2', email='same@example.com', password='pass1234'
            )

    def test_str_representation(self):
        user = User.objects.create_user(
            username='testuser', email='test@example.com', password='pass1234'
        )
        self.assertEqual(str(user), 'test@example.com (user)')

    def test_must_change_password_flag(self):
        user = User.objects.create_user(
            username='testuser', email='test@example.com',
            password='pass1234', must_change_password=True
        )
        self.assertTrue(user.must_change_password)
