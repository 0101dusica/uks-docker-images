from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
        ('superadmin', 'Superadmin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email} ({self.role})"