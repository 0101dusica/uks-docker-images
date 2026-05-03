from rest_framework import serializers
from .models import Repository


class PublicRepositorySerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source='owner.username', read_only=True)
    owner_badge = serializers.CharField(source='owner.badge', read_only=True)

    class Meta:
        model = Repository
        fields = ['id', 'name', 'description', 'owner', 'owner_badge', 'is_official', 'stars', 'created_at', 'updated_at']
