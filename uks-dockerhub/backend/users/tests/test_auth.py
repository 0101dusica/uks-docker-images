from django.test import TestCase, Client
from django.urls import reverse
from users.models import User


class LoginTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='pass1234'
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_successful_login_redirects_user(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser', 'password': 'pass1234'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login-success'))

    def test_admin_login_redirects_to_admin_dashboard(self):
        admin = User.objects.create_user(
            username='admin1', email='admin@example.com',
            password='pass1234', role='admin'
        )
        response = self.client.post(reverse('login'), {
            'username': 'admin1', 'password': 'pass1234'
        })
        self.assertRedirects(response, reverse('admin-dashboard'))

    def test_superadmin_login_redirects_to_superadmin_dashboard(self):
        superadmin = User.objects.create_user(
            username='super1', email='super@example.com',
            password='pass1234', role='superadmin'
        )
        response = self.client.post(reverse('login'), {
            'username': 'super1', 'password': 'pass1234'
        })
        self.assertRedirects(response, reverse('superadmin-dashboard'))

    def test_login_with_wrong_password(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser', 'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

    def test_login_with_nonexistent_user(self):
        response = self.client.post(reverse('login'), {
            'username': 'nouser', 'password': 'pass1234'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

    def test_blocked_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(reverse('login'), {
            'username': 'testuser', 'password': 'pass1234'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account_blocked.html')

    def test_logout(self):
        self.client.login(username='testuser', password='pass1234')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)


class RegistrationViewTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_registration_page_loads(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_successful_registration(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertRedirects(response, reverse('registration-success'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_registration_with_mismatched_passwords(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'StrongPass123!',
            'password2': 'DifferentPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())


class ForcePasswordChangeTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='forceuser', email='force@example.com',
            password='oldpass1234', must_change_password=True
        )
        self.client.login(username='forceuser', password='oldpass1234')

    def test_redirect_to_password_change(self):
        response = self.client.get(reverse('login-success'))
        self.assertRedirects(response, reverse('force-password-change'))

    def test_can_access_password_change_page(self):
        response = self.client.get(reverse('force-password-change'))
        self.assertEqual(response.status_code, 200)

    def test_can_access_logout_while_forced(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)

    def test_successful_password_change(self):
        response = self.client.post(reverse('force-password-change'), {
            'new_password': 'newpass12345',
            'confirm_password': 'newpass12345',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertFalse(self.user.must_change_password)

    def test_password_change_too_short(self):
        response = self.client.post(reverse('force-password-change'), {
            'new_password': 'short',
            'confirm_password': 'short',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'at least 8 characters')

    def test_password_change_mismatch(self):
        response = self.client.post(reverse('force-password-change'), {
            'new_password': 'newpass12345',
            'confirm_password': 'different12345',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'do not match')
