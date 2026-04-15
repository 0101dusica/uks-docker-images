import logging

from django.contrib.auth import login, logout
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
    repositories = Repository.objects.filter(visibility='public')

    search = request.GET.get('search', '').strip()
    if search:
        from django.db.models import Q
        repositories = repositories.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    badge_filter = request.GET.get('badge', '').strip()
    if badge_filter == 'official':
        repositories = repositories.filter(is_official=True)
    elif badge_filter in ('verified_publisher', 'sponsored_oss'):
        repositories = repositories.filter(owner__badge=badge_filter)

    sort = request.GET.get('sort', 'newest')
    if sort == 'stars':
        repositories = repositories.order_by('-stars', '-created_at')
    elif sort == 'name':
        repositories = repositories.order_by('name')
    else:
        repositories = repositories.order_by('-created_at')

    starred_ids = set()
    if request.user.is_authenticated:
        starred_ids = set(
            Star.objects.filter(user=request.user, repository__in=repositories)
            .values_list('repository_id', flat=True)
        )
    return render(request, 'public_repositories.html', {
        'repositories': repositories,
        'starred_ids': starred_ids,
        'search': search,
        'badge_filter': badge_filter,
        'sort': sort,
    })


@login_required(login_url='login')
def my_repositories_view(request):
    repositories = Repository.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'my_repositories.html', {'repositories': repositories})


@login_required(login_url='login')
def create_repository_view(request):
    if request.method == 'POST':
        form = RepositoryCreateForm(request.POST, owner=request.user)
        if form.is_valid():
            repo = form.save()
            logger.info(
                "Repository created",
                extra={"repo_id": str(repo.id), "repo_name": repo.name, "owner_id": str(request.user.id)},
            )
            _invalidate_repo_cache()
            return redirect('my-repositories')
    else:
        form = RepositoryCreateForm(owner=request.user)
    return render(request, 'create_repository.html', {'form': form})


@login_required(login_url='login')
def edit_repository_view(request, repo_id):
    repo = Repository.objects.get(id=repo_id)
    if repo.owner != request.user:
        logger.warning(
            "Unauthorized repository edit attempt",
            extra={"repo_id": str(repo_id), "user_id": str(request.user.id)},
        )
        return HttpResponseForbidden('You can only edit your own repositories.')
    if request.method == 'POST':
        form = RepositoryEditForm(request.POST, instance=repo)
        if form.is_valid():
            form.save()
            logger.info(
                "Repository edited",
                extra={"repo_id": str(repo.id), "repo_name": repo.name, "owner_id": str(request.user.id)},
            )
            _invalidate_repo_cache()
            return redirect('my-repositories')
    else:
        form = RepositoryEditForm(instance=repo)
    return render(request, 'edit_repository.html', {'form': form, 'repo': repo})


@csrf_exempt
@login_required(login_url='login')
def delete_repository_view(request, repo_id):
    if request.method == 'POST':
        repo = Repository.objects.get(id=repo_id)
        if repo.owner != request.user:
            logger.warning(
                "Unauthorized repository delete attempt",
                extra={"repo_id": str(repo_id), "user_id": str(request.user.id)},
            )
            return HttpResponseForbidden('You can only delete your own repositories.')
        logger.info(
            "Repository deleted",
            extra={"repo_id": str(repo.id), "repo_name": repo.name, "owner_id": str(request.user.id)},
        )
        repo.delete()
        _invalidate_repo_cache()
        return redirect('my-repositories')
    return HttpResponseForbidden()


@csrf_exempt
@login_required(login_url='login')
def toggle_star_view(request, repo_id):
    if request.method == 'POST':
        repo = Repository.objects.get(id=repo_id)
        star, created = Star.objects.get_or_create(user=request.user, repository=repo)
        if not created:
            star.delete()
            repo.stars = Star.objects.filter(repository=repo).count()
            logger.info(
                "Repository unstarred",
                extra={"repo_id": str(repo.id), "user_id": str(request.user.id)},
            )
        else:
            repo.stars = Star.objects.filter(repository=repo).count()
            logger.info(
                "Repository starred",
                extra={"repo_id": str(repo.id), "user_id": str(request.user.id)},
            )
        repo.save()
        _invalidate_repo_cache()
        return redirect('public-repositories')
    return HttpResponseForbidden()


@login_required(login_url='login')
def manage_tags_view(request, repo_id):
    repo = Repository.objects.get(id=repo_id)
    if repo.owner != request.user:
        return HttpResponseForbidden('You can only manage tags on your own repositories.')
    error = None
    if request.method == 'POST' and 'add_tag' in request.POST:
        tag_name = request.POST.get('tag_name', '').strip()
        if not tag_name:
            error = 'Tag name cannot be empty.'
        elif Tag.objects.filter(repository=repo, name=tag_name).exists():
            error = 'This tag already exists.'
        else:
            Tag.objects.create(repository=repo, name=tag_name)
            return redirect('manage-tags', repo_id=repo.id)
    tags = Tag.objects.filter(repository=repo).order_by('-created_at')

    # Fetch tags from container registry
    registry = RegistryService()
    registry_repo_name = f'{repo.owner.username}/{repo.name}'
    registry_tags = registry.get_tags(registry_repo_name)

    return render(request, 'manage_tags.html', {
        'repo': repo,
        'tags': tags,
        'registry_tags': registry_tags,
        'error': error,
    })


@csrf_exempt
@login_required(login_url='login')
def delete_tag_view(request, repo_id, tag_id):
    if request.method == 'POST':
        repo = Repository.objects.get(id=repo_id)
        if repo.owner != request.user:
            logger.warning(
                "Unauthorized tag delete attempt",
                extra={"repo_id": str(repo_id), "tag_id": str(tag_id), "user_id": str(request.user.id)},
            )
            return HttpResponseForbidden('You can only delete tags on your own repositories.')
        logger.info(
            "Tag deleted",
            extra={"repo_id": str(repo.id), "tag_id": str(tag_id), "owner_id": str(request.user.id)},
        )
        Tag.objects.filter(id=tag_id, repository=repo).delete()
        return redirect('manage-tags', repo_id=repo.id)
    return HttpResponseForbidden()


@csrf_exempt
@login_required(login_url='login')
def delete_registry_tag_view(request, repo_id, tag_name):
    if request.method == 'POST':
        repo = Repository.objects.get(id=repo_id)
        if repo.owner != request.user:
            logger.warning(
                "Unauthorized registry tag delete attempt",
                extra={"repo_id": str(repo_id), "tag_name": tag_name, "user_id": str(request.user.id)},
            )
            return HttpResponseForbidden('You can only delete tags on your own repositories.')
        registry = RegistryService()
        registry_repo_name = f'{repo.owner.username}/{repo.name}'
        digest = registry.get_tag_digest(registry_repo_name, tag_name)
        if digest:
            registry.delete_manifest(registry_repo_name, digest)
            logger.info(
                "Registry tag deleted",
                extra={"repo_id": str(repo.id), "tag_name": tag_name, "owner_id": str(request.user.id)},
            )
        return redirect('manage-tags', repo_id=repo.id)
    return HttpResponseForbidden()


@login_required(login_url='login')
def profile_view(request):
    error = None
    success = None
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        if not email:
            error = 'Email is required.'
        elif User.objects.filter(email=email).exclude(id=request.user.id).exists():
            error = 'This email is already taken.'
        else:
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.email = email
            request.user.save()
            success = 'Profile updated successfully.'
    return render(request, 'profile.html', {
        'error': error,
        'success': success,
    })


@login_required(login_url='login')
def starred_repos_view(request):
    starred = Star.objects.filter(user=request.user).select_related('repository', 'repository__owner').order_by('-created_at')
    repositories = [s.repository for s in starred]
    return render(request, 'starred_repos.html', {'repositories': repositories})


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