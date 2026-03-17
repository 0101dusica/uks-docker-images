from django.db import models
from django.conf import settings


class Badge(models.TextChoices):
    DOCKER_OFFICIAL_IMAGE = "DOCKER_OFFICIAL_IMAGE", "Docker Official Image"
    VERIFIED_PUBLISHER = "VERIFIED_PUBLISHER", "Verified Publisher"
    SPONSORED_OSS = "SPONSORED_OSS", "Sponsored OSS"


class Repository(models.Model):

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    is_public = models.BooleanField(default=True, db_index=True)
    stars = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_public", "name"]),
        ]

    def __str__(self) -> str:
        return self.name





