from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/repositories/', include('repositories.urls')),
    path('accounts/', include('frontend.urls')),
    path('', include('frontend.urls')),
    path('', include('analytics.urls')),
]
