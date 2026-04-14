from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Repository
from .serializers import PublicRepositorySerializer


class PublicRepositoriesView(APIView):
    def get(self, request):
        repos = Repository.objects.filter(visibility='public')

        search = request.query_params.get('search', '').strip()
        if search:
            from django.db.models import Q
            repos = repos.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        badge = request.query_params.get('badge', '').strip()
        if badge == 'official':
            repos = repos.filter(is_official=True)
        elif badge in ('verified_publisher', 'sponsored_oss'):
            repos = repos.filter(owner__badge=badge)

        sort = request.query_params.get('sort', 'newest')
        if sort == 'stars':
            repos = repos.order_by('-stars', '-created_at')
        elif sort == 'name':
            repos = repos.order_by('name')
        else:
            repos = repos.order_by('-created_at')

        serializer = PublicRepositorySerializer(repos, many=True)
        return Response(
            {'count': repos.count(), 'results': serializer.data},
            status=status.HTTP_200_OK,
        )
