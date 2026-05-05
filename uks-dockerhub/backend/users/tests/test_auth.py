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


class ProfileTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com',
            password='pass1234', first_name='Test', last_name='User'
        )
        self.client.login(username='testuser', password='pass1234')

    def test_profile_page_loads(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'test@example.com')

    def test_update_profile(self):
        response = self.client.post(reverse('profile'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'new@example.com',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Profile updated successfully')
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.email, 'new@example.com')

    def test_duplicate_email_rejected(self):
        User.objects.create_user(
            username='other', email='taken@example.com', password='pass1234'
        )
        response = self.client.post(reverse('profile'), {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'taken@example.com',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already taken')

    def test_unauthenticated_redirected(self):
        self.client.logout()
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)


class StarredReposTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='staruser', email='star@example.com', password='pass1234'
        )
        self.owner = User.objects.create_user(
            username='owner', email='owner@example.com', password='pass1234'
        )
        self.client.login(username='staruser', password='pass1234')

    def test_starred_page_loads(self):
        response = self.client.get(reverse('starred-repos'))
        self.assertEqual(response.status_code, 200)

    def test_shows_starred_repos(self):
        from repositories.models import Repository, Star
        repo = Repository.objects.create(
            name='liked', owner=self.owner, visibility='public'
        )
        Star.objects.create(user=self.user, repository=repo)
        response = self.client.get(reverse('starred-repos'))
        self.assertContains(response, 'liked')

    def test_does_not_show_unstarred_repos(self):
        from repositories.models import Repository
        Repository.objects.create(
            name='notstarred', owner=self.owner, visibility='public'
        )
        response = self.client.get(reverse('starred-repos'))
        self.assertNotContains(response, 'notstarred')

    def test_empty_starred_message(self):
        response = self.client.get(reverse('starred-repos'))
        self.assertContains(response, "haven't starred any")


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
