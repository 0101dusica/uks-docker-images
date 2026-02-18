from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User

class UserRegistrationTests(APITestCase):
    def setUp(self):
        self.url = reverse('user-register')
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'StrongPassword123!'
        }

    def test_successful_registration(self):
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, self.user_data['email'])

    def test_duplicate_email_registration(self):
        User.objects.create_user(
            email=self.user_data['email'],
            username='otheruser',
            password='SomePassword123!'
        )
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_invalid_data_registration(self):
        invalid_data = self.user_data.copy()
        invalid_data['email'] = 'not-an-email'
        response = self.client.post(self.url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
