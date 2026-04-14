import logging

from django.core.cache import cache

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Repository
from .serializers import PublicRepositorySerializer
from .registry import RegistryService

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 5  # 5 minutes


class PublicRepositoriesView(APIView):
    def get(self, request):
        search = request.query_params.get('search', '').strip()
        badge = request.query_params.get('badge', '').strip()
        sort = request.query_params.get('sort', 'newest')

        cache_key = f'public_repos:{search}:{badge}:{sort}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached, status=status.HTTP_200_OK)

        repos = Repository.objects.filter(visibility='public')

        if search:
            from django.db.models import Q
            repos = repos.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        if badge == 'official':
            repos = repos.filter(is_official=True)
        elif badge in ('verified_publisher', 'sponsored_oss'):
            repos = repos.filter(owner__badge=badge)

        if sort == 'stars':
            repos = repos.order_by('-stars', '-created_at')
        elif sort == 'name':
            repos = repos.order_by('name')
        else:
            repos = repos.order_by('-created_at')

        serializer = PublicRepositorySerializer(repos, many=True)
        result = {'count': repos.count(), 'results': serializer.data}
        cache.set(cache_key, result, CACHE_TTL)
        return Response(result, status=status.HTTP_200_OK)


class RegistryCatalogView(APIView):
    """List all repositories in the container registry."""

    def get(self, request):
        registry = RegistryService()
        repositories = registry.get_catalog()
        if repositories is None:
            logger.error("Failed to fetch registry catalog")
            repositories = []
        else:
            logger.info("Registry catalog fetched", extra={"count": len(repositories)})
        return Response({'repositories': repositories}, status=status.HTTP_200_OK)


class RegistryTagsView(APIView):
    """List tags for a repository from the container registry."""

    def get(self, request, repo_name):
        registry = RegistryService()
        tags = registry.get_tags(repo_name)

        if tags is None:
            logger.error("Failed to fetch registry tags", extra={"repo_name": repo_name})
            tags = []
        else:
            logger.info("Registry tags fetched", extra={"repo_name": repo_name, "count": len(tags)})

        tag_details = []
        for tag in tags:
            manifest = registry.get_manifest(repo_name, tag)
            tag_details.append({
                'name': tag,
                'digest': manifest.get('digest', '') if manifest else '',
                'size': manifest.get('size', 0) if manifest else 0,
            })

        return Response({
            'repository': repo_name,
            'tags': tag_details,
        }, status=status.HTTP_200_OK)
