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
    BADGE_CHOICES = (
        ('none', 'None'),
        ('verified_publisher', 'Verified Publisher'),
        ('sponsored_oss', 'Sponsored OSS'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    badge = models.CharField(max_length=30, choices=BADGE_CHOICES, default='none')
    must_change_password = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return f"{self.email} ({self.role})"