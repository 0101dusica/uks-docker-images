from django.urls import path
from .views import registration_view, registration_success_view

urlpatterns = [
    path('', registration_view, name='register'),
    path('register/', registration_view, name='register'),
    path('register/success/', registration_success_view, name='registration-success'),
]
