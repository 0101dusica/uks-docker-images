from django.urls import path
from .views import PublicRepositoriesView, RegistryCatalogView, RegistryTagsView

urlpatterns = [
    path('public/', PublicRepositoriesView.as_view(), name='api-public-repositories'),
    path('registry/catalog/', RegistryCatalogView.as_view(), name='registry-catalog'),
    path('registry/<path:repo_name>/tags/', RegistryTagsView.as_view(), name='registry-tags'),
]
