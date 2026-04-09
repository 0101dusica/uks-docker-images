import logging
import os
import secrets
import string

from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver

logger = logging.getLogger(__name__)

SUPERADMIN_USERNAME = 'superadmin'
SUPERADMIN_EMAIL = 'superadmin@example.com'
PASSWORD_FILE_NAME = 'superadmin_initial_password.txt'


def generate_password(length=16):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def write_password_file(password):
    password_file_path = os.path.join(settings.BASE_DIR, PASSWORD_FILE_NAME)
    with open(password_file_path, 'w') as f:
        f.write(f'Superadmin initial credentials\n')
        f.write(f'Username: {SUPERADMIN_USERNAME}\n')
        f.write(f'Password: {password}\n')
        f.write(f'\nPlease change this password on first login.\n')
    os.chmod(password_file_path, 0o600)
    logger.info('Superadmin initial password written to %s', password_file_path)


@receiver(post_migrate)
def create_superadmin(sender, **kwargs):
    if sender.name != 'users':
        return

    from users.models import User

    if User.objects.filter(role='superadmin').exists():
        logger.info('Superadmin account already exists, skipping creation.')
        return

    password = generate_password()

    User.objects.create_superuser(
        username=SUPERADMIN_USERNAME,
        email=SUPERADMIN_EMAIL,
        password=password,
        first_name='Super',
        last_name='Admin',
        role='superadmin',
        is_active=True,
        must_change_password=True,
    )
    write_password_file(password)
    logger.info('Superadmin account created successfully on first startup.')
