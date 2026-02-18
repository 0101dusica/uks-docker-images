import os
from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from users.models import User

def get_superadmin_password():
    return os.environ.get('SUPERADMIN_PASSWORD', 'superadmin123')

@receiver(post_migrate)
def create_superadmin(sender, **kwargs):
    if not User.objects.filter(username='superadmin').exists():
        User.objects.create_superuser(
            username='superadmin',
            email='superadmin@example.com',
            password=get_superadmin_password(),
            first_name='Super',
            last_name='Admin',
            role='superadmin',
            is_active=True
        )
