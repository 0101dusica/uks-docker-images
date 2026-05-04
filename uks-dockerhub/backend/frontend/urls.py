from django.urls import path
from .views import registration_view, registration_success_view, login_view, login_success_view, admin_dashboard_view, \
    superadmin_dashboard_view, user_details_view, repository_detail_view, block_user_view, unblock_user_view, \
    assign_badge_view, edit_official_repository_view, delete_official_repository_view, delete_registry_tag_view, \
    superadmin_user_details_view, superadmin_user_block_view, superadmin_user_unblock_view, \
    superadmin_admin_details_view, superadmin_admin_block_view, superadmin_admin_unblock_view, logout_view, \
    public_repositories_view, force_password_change_view, my_repositories_view, create_repository_view, \
    edit_repository_view, delete_repository_view, toggle_star_view, manage_tags_view, delete_tag_view, \
    profile_view, starred_repos_view

urlpatterns = [
    path('', registration_view, name='register'),
    path('register/', registration_view, name='register'),
    path('register/success/', registration_success_view, name='registration-success'),
    path('login/', login_view, name='login'),
    path('login/success/', login_success_view, name='login-success'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('starred/', starred_repos_view, name='starred-repos'),
    path('change-password/', force_password_change_view, name='force-password-change'),
    path('admin-dashboard/', admin_dashboard_view, name='admin-dashboard'),
    path('superadmin-dashboard/', superadmin_dashboard_view, name='superadmin-dashboard'),
    path('admin-dashboard/user/<int:user_id>/details/', user_details_view, name='user-details'),
    path('admin-dashboard/user/<int:user_id>/block/', block_user_view, name='block-user'),
    path('admin-dashboard/user/<int:user_id>/unblock/', unblock_user_view, name='unblock-user'),
    path('admin-dashboard/user/<int:user_id>/assign-badge/', assign_badge_view, name='assign-badge'),
    path('admin-dashboard/official/<int:repo_id>/edit/', edit_official_repository_view, name='edit-official-repo'),
    path('admin-dashboard/official/<int:repo_id>/delete/', delete_official_repository_view, name='delete-official-repo'),
    # Superadmin dashboard detalji/blokiranje
    path('superadmin-dashboard/user/<int:user_id>/details/', superadmin_user_details_view, name='superadmin-user-details'),
    path('superadmin-dashboard/user/<int:user_id>/block/', superadmin_user_block_view, name='superadmin-user-block'),
    path('superadmin-dashboard/user/<int:user_id>/unblock/', superadmin_user_unblock_view, name='superadmin-user-unblock'),
    path('superadmin-dashboard/admin/<int:admin_id>/details/', superadmin_admin_details_view, name='superadmin-admin-details'),
    path('superadmin-dashboard/admin/<int:admin_id>/block/', superadmin_admin_block_view, name='superadmin-admin-block'),
    path('superadmin-dashboard/admin/<int:admin_id>/unblock/', superadmin_admin_unblock_view, name='superadmin-admin-unblock'),
    path('public-repositories/', public_repositories_view, name='public-repositories'),
    path('repository/<int:id>/', repository_detail_view, name='repository-detail'),
    path('my-repositories/', my_repositories_view, name='my-repositories'),
    path('repositories/create/', create_repository_view, name='create-repository'),
    path('repositories/<int:repo_id>/edit/', edit_repository_view, name='edit-repository'),
    path('repositories/<int:repo_id>/delete/', delete_repository_view, name='delete-repository'),
    path('repositories/<int:repo_id>/star/', toggle_star_view, name='toggle-star'),
    path('repositories/<int:repo_id>/tags/', manage_tags_view, name='manage-tags'),
    path('repositories/<int:repo_id>/tags/<int:tag_id>/delete/', delete_tag_view, name='delete-tag'),
    path('repositories/<int:repo_id>/registry-tags/<str:tag_name>/delete/', delete_registry_tag_view, name='delete-registry-tag'),

]
