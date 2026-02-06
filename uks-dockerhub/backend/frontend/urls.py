from django.urls import path
from .views import registration_view, registration_success_view, login_view, login_success_view

urlpatterns = [
    path('', registration_view, name='register'),
    path('register/', registration_view, name='register'),
    path('register/success/', registration_success_view, name='registration-success'),
    path('login/', login_view, name='login'),
    path('login/success/', login_success_view, name='login-success'),
]
