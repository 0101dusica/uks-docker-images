from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Repository
from .serializers import PublicRepositorySerializer


class PublicRepositoriesView(APIView):
    def get(self, request):
        repos = Repository.objects.filter(visibility='public').order_by('-created_at')
        serializer = PublicRepositorySerializer(repos, many=True)
        return Response(
            {'count': repos.count(), 'results': serializer.data},
            status=status.HTTP_200_OK,
        )
