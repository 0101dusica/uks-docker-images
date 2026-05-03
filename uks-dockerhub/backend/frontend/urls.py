from django.urls import path
from .views import registration_view, registration_success_view, login_view, login_success_view, admin_dashboard_view, \
    superadmin_dashboard_view, user_details_view, block_user_view, superadmin_user_details_view, \
    superadmin_user_block_view, superadmin_admin_details_view, superadmin_admin_block_view, logout_view, \
    public_repositories_view, force_password_change_view

urlpatterns = [
    path('', registration_view, name='register'),
    path('register/', registration_view, name='register'),
    path('register/success/', registration_success_view, name='registration-success'),
    path('login/', login_view, name='login'),
    path('login/success/', login_success_view, name='login-success'),
    path('logout/', logout_view, name='logout'),
    path('change-password/', force_password_change_view, name='force-password-change'),
    path('admin-dashboard/', admin_dashboard_view, name='admin-dashboard'),
    path('superadmin-dashboard/', superadmin_dashboard_view, name='superadmin-dashboard'),
    path('admin-dashboard/user/<int:user_id>/details/', user_details_view, name='user-details'),
    path('admin-dashboard/user/<int:user_id>/block/', block_user_view, name='block-user'),
    # Superadmin dashboard detalji/blokiranje
    path('superadmin-dashboard/user/<int:user_id>/details/', superadmin_user_details_view, name='superadmin-user-details'),
    path('superadmin-dashboard/user/<int:user_id>/block/', superadmin_user_block_view, name='superadmin-user-block'),
    path('superadmin-dashboard/admin/<int:admin_id>/details/', superadmin_admin_details_view, name='superadmin-admin-details'),
    path('superadmin-dashboard/admin/<int:admin_id>/block/', superadmin_admin_block_view, name='superadmin-admin-block'),
    path('public-repositories/', public_repositories_view, name='public-repositories'),
    path('repository/<int:id>/', repository_detail_view, name='repository-detail')
]
