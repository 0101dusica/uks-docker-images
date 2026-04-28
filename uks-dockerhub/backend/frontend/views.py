import logging

from django.contrib.auth import login, logout
from django.db.models import Q
from django.core.cache import cache

logger = logging.getLogger(__name__)

from repositories.forms import RepositoryCreateForm, RepositoryEditForm, OfficialRepositoryCreateForm
from repositories.models import Repository, Star
from repositories.registry import RegistryService
from tags.models import Tag


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect


def _invalidate_repo_cache():
    cache.delete_pattern('public_repos:*')
from django.views.decorators.csrf import csrf_exempt

from users.forms import CustomUserCreationForm, CustomLoginForm
from users.models import User
from users.permissions import admin_required, superadmin_required


def logout_view(request):
    if request.user.is_authenticated:
        logger.info("User logged out", extra={"username": request.user.username, "user_id": str(request.user.id)})
    logout(request)
    return redirect('login')

def login_view(request):
    error = None
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
                if not user.is_active:
                    logger.warning(
                        "Login attempt by blocked user",
                        extra={"username": user.username, "user_id": str(user.id)},
                    )
                    return render(request, 'account_blocked.html')
                from django.contrib.auth.hashers import check_password
                if check_password(password, user.password):
                    login(request, user)
                    logger.info(
                        "User logged in",
                        extra={"username": user.username, "user_id": str(user.id), "role": user.role},
                    )
                    if user.role == 'admin':
                        return redirect('admin-dashboard')
                    elif user.role == 'superadmin':
                        return redirect('superadmin-dashboard')
                    else:
                        return redirect('login-success')
                else:
                    logger.warning("Failed login attempt", extra={"username_attempted": username})
                    error = "Invalid username or password."
            except User.DoesNotExist:
                logger.warning("Failed login attempt", extra={"username_attempted": username})
                error = "Invalid username or password."
        else:
            error = "Invalid username or password."
    else:
        form = CustomLoginForm()
    return render(request, 'login.html', {'form': form, 'error': error})

def registration_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info("New user registered", extra={"username": user.username, "user_id": str(user.id)})
            return redirect('registration-success')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration.html', {'form': form})

def registration_success_view(request):
    return render(request, 'registration_success.html')

def login_success_view(request):
    return render(request, 'login_success.html')

@admin_required
def admin_dashboard_view(request):
    users = User.objects.filter(role='user')

    user_search = request.GET.get('user_search', '').strip()
    if user_search:
        from django.db.models import Q
        users = users.filter(
            Q(username__icontains=user_search) |
            Q(email__icontains=user_search) |
            Q(first_name__icontains=user_search) |
            Q(last_name__icontains=user_search)
        )

    official_repos = Repository.objects.filter(is_official=True).order_by('-created_at')
    official_form_error = None

    if request.method == 'POST' and 'create_official' in request.POST:
        form = OfficialRepositoryCreateForm(request.POST)
        if form.is_valid():
            repo = form.save(owner=request.user)
            logger.info(
                "Official repository created",
                extra={"repo_id": str(repo.id), "repo_name": repo.name, "admin_id": str(request.user.id)},
            )
            _invalidate_repo_cache()
            return redirect('admin-dashboard')
        else:
            official_form_error = form.errors.as_text()
    else:
        form = OfficialRepositoryCreateForm()

    return render(request, 'admin_dashboard.html', {
        'users': users,
        'user_search': user_search,
        'official_repos': official_repos,
        'official_form': form,
        'official_form_error': official_form_error,
    })

@admin_required
def edit_official_repository_view(request, repo_id):
    try:
        repo = Repository.objects.get(id=repo_id, is_official=True)
    except Repository.DoesNotExist:
        return HttpResponseForbidden('Official repository not found.')
    if request.method == 'POST':
        form = RepositoryEditForm(request.POST, instance=repo)
        if form.is_valid():
            form.save()
            logger.info(
                "Official repository edited",
                extra={"repo_id": str(repo.id), "repo_name": repo.name, "admin_id": str(request.user.id)},
            )
            _invalidate_repo_cache()
            return redirect('admin-dashboard')
    else:
        form = RepositoryEditForm(instance=repo)
    return render(request, 'edit_official_repository.html', {'form': form, 'repo': repo})


@csrf_exempt
@admin_required
def delete_official_repository_view(request, repo_id):
    if request.method == 'POST':
        try:
            repo = Repository.objects.get(id=repo_id, is_official=True)
            logger.info(
                "Official repository deleted",
                extra={"repo_id": str(repo.id), "repo_name": repo.name, "admin_id": str(request.user.id)},
            )
            repo.delete()
            _invalidate_repo_cache()
            return redirect('admin-dashboard')
        except Repository.DoesNotExist:
            return HttpResponseForbidden('Official repository not found.')
    return HttpResponseForbidden()


@admin_required
def user_details_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        data = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'status': 'Active' if user.is_active else 'Blocked',
            'badge': user.badge,
        }
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@csrf_exempt
@admin_required
def assign_badge_view(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id, role='user')
            import json
            body = json.loads(request.body)
            badge = body.get('badge', 'none')
            if badge not in ('none', 'verified_publisher', 'sponsored_oss'):
                return JsonResponse({'error': 'Invalid badge'}, status=400)
            user.badge = badge
            user.save()
            logger.info(
                "Badge assigned to user",
                extra={"target_user_id": str(user.id), "badge": badge, "admin_id": str(request.user.id)},
            )
            _invalidate_repo_cache()
            return JsonResponse({'success': True, 'badge': user.badge})
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    return HttpResponseForbidden()

@csrf_exempt
@admin_required
def block_user_view(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            user.is_active = False
            user.save()
            logger.info(
                "User blocked",
                extra={"target_user_id": str(user.id), "target_username": user.username, "admin_id": str(request.user.id)},
            )
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    return HttpResponseForbidden()

@superadmin_required
def superadmin_dashboard_view(request):
    users = User.objects.filter(role='user')
    admins = User.objects.filter(role='admin')

    user_search = request.GET.get('user_search', '').strip()
    if user_search:
        from django.db.models import Q
        users = users.filter(
            Q(username__icontains=user_search) |
            Q(email__icontains=user_search) |
            Q(first_name__icontains=user_search) |
            Q(last_name__icontains=user_search)
        )
        admins = admins.filter(
            Q(username__icontains=user_search) |
            Q(email__icontains=user_search) |
            Q(first_name__icontains=user_search) |
            Q(last_name__icontains=user_search)
        )

    admin_form_error = None
    if request.method == 'POST' and 'add_admin' in request.POST:
        # Dodavanje novog admina
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            new_admin = form.save(commit=False)
            new_admin.role = 'admin'
            new_admin.is_active = True
            new_admin.save()
            logger.info(
                "New admin created",
                extra={"new_admin_id": str(new_admin.id), "new_admin_username": new_admin.username, "superadmin_id": str(request.user.id)},
            )
            return redirect('superadmin-dashboard')
        else:
            admin_form_error = form.errors.as_text()
    else:
        form = CustomUserCreationForm()
    return render(request, 'superadmin_dashboard.html', {
        'users': users,
        'admins': admins,
        'user_search': user_search,
        'admin_form': form,
        'admin_form_error': admin_form_error,
    })

@superadmin_required
def superadmin_user_details_view(request, user_id):
    try:
        user = User.objects.get(id=user_id, role='user')
        data = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'status': 'Active' if user.is_active else 'Blocked',
        }
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@csrf_exempt
@superadmin_required
def superadmin_user_block_view(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id, role='user')
            user.is_active = False
            user.save()
            logger.info(
                "User blocked by superadmin",
                extra={"target_user_id": str(user.id), "target_username": user.username, "superadmin_id": str(request.user.id)},
            )
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    return HttpResponseForbidden()

@superadmin_required
def superadmin_admin_details_view(request, admin_id):
    try:
        admin = User.objects.get(id=admin_id, role='admin')
        data = {
            'username': admin.username,
            'first_name': admin.first_name,
            'last_name': admin.last_name,
            'email': admin.email,
            'status': 'Active' if admin.is_active else 'Blocked',
        }
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Admin not found'}, status=404)

@csrf_exempt
@superadmin_required
def superadmin_admin_block_view(request, admin_id):
    if request.method == 'POST':
        try:
            admin = User.objects.get(id=admin_id, role='admin')
            admin.is_active = False
            admin.save()
            logger.info(
                "Admin blocked by superadmin",
                extra={"target_admin_id": str(admin.id), "target_username": admin.username, "superadmin_id": str(request.user.id)},
            )
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'error': 'Admin not found'}, status=404)
    return HttpResponseForbidden()

def public_repositories_view(request):
    query = request.GET.get('q', '').strip()
    repositories = Repository.objects.filter(visibility='public')

    if query:
        repositories = repositories.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
        repositories = repositories.order_by('-stars', '-created_at')
    else:
        repositories = repositories.order_by('-created_at')

    return render(request, 'public_repositories.html', {
        'repositories': repositories,
        'query': query
    })

@login_required(login_url='login')
def force_password_change_view(request):
    error = None
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not new_password or len(new_password) < 8:
            error = 'Password must be at least 8 characters long.'
        elif new_password != confirm_password:
            error = 'Passwords do not match.'
        else:
            request.user.set_password(new_password)
            request.user.must_change_password = False
            request.user.save()
            login(request, request.user)
            logger.info(
                "User changed password",
                extra={"user_id": str(request.user.id), "username": request.user.username},
            )
            if request.user.role == 'superadmin':
                return redirect('superadmin-dashboard')
            elif request.user.role == 'admin':
                return redirect('admin-dashboard')
            else:
                return redirect('login-success')
    return render(request, 'force_password_change.html', {'error': error})