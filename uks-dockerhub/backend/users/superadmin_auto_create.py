import logging
import os

from django.db.models.signals import post_migrate
from django.dispatch import receiver

logger = logging.getLogger(__name__)

SUPERADMIN_USERNAME = 'superadmin'
SUPERADMIN_EMAIL = 'superadmin@example.com'


@receiver(post_migrate)
def create_superadmin(sender, **kwargs):
    if sender.name != 'users':
        return

    from users.models import User

    if User.objects.filter(role='superadmin').exists():
        logger.info('Superadmin account already exists, skipping creation.')
        return

    password = os.environ.get('SUPERADMIN_PASSWORD', 'superadmin123')

    User.objects.create_superuser(
        username=SUPERADMIN_USERNAME,
        email=SUPERADMIN_EMAIL,
        password=password,
        first_name='Super',
        last_name='Admin',
        role='superadmin',
        is_active=True,
    )
    logger.info('Superadmin account created successfully on first startup.')
