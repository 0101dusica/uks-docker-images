from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Repository


class PublicRepositoriesView(APIView):


    def get(self, request):
        repos = Repository.objects.filter(is_public=True).order_by("-created_at")

        results = [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "stars": r.stars,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
            for r in repos
        ]

        return Response(
            {"count": repos.count(), "results": results},
            status=status.HTTP_200_OK,
        )


from rest_framework.views import APIView

# Create your views here.
