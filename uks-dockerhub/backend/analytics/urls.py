from django.urls import path

from .views import analytics_search_view

urlpatterns = [
    path('analytics/', analytics_search_view, name='analytics-search'),
]
