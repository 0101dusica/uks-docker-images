from django.db import models
from repositories.models import Repository


class Tag(models.Model):
    name = models.CharField(max_length=255)
    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name='tags',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['repository', 'name'],
                name='unique_tag_per_repo',
            ),
        ]

    def __str__(self):
        return f"{self.repository.name}:{self.name}"
