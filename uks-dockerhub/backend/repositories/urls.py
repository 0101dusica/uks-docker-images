from django.urls import path

from django.urls import path
from .views import PublicRepositoriesView

urlpatterns = [
    path("public/", PublicRepositoriesView.as_view(), name="public-repositories"),
]
