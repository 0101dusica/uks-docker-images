from django.contrib.auth import login, logout

from repositories.forms import RepositoryCreateForm
from repositories.models import Repository


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from users.forms import CustomUserCreationForm, CustomLoginForm
from users.models import User
from users.permissions import admin_required, superadmin_required


def logout_view(request):
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
                    return render(request, 'account_blocked.html')
                from django.contrib.auth.hashers import check_password
                if check_password(password, user.password):
                    login(request, user)
                    if user.role == 'admin':
                        return redirect('admin-dashboard')
                    elif user.role == 'superadmin':
                        return redirect('superadmin-dashboard')
                    else:
                        return redirect('login-success')
                else:
                    error = "Invalid username or password."
            except User.DoesNotExist:
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
            form.save()
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
    return render(request, 'admin_dashboard.html', {'users': users})

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
        }
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@csrf_exempt
@admin_required
def block_user_view(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            user.is_active = False
            user.save()
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    return HttpResponseForbidden()

@superadmin_required
def superadmin_dashboard_view(request):
    users = User.objects.filter(role='user')
    admins = User.objects.filter(role='admin')
    admin_form_error = None
    if request.method == 'POST' and 'add_admin' in request.POST:
        # Dodavanje novog admina
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            new_admin = form.save(commit=False)
            new_admin.role = 'admin'
            new_admin.is_active = True
            new_admin.save()
            return redirect('superadmin-dashboard')
        else:
            admin_form_error = form.errors.as_text()
    else:
        form = CustomUserCreationForm()
    return render(request, 'superadmin_dashboard.html', {
        'users': users,
        'admins': admins,
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
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'error': 'Admin not found'}, status=404)
    return HttpResponseForbidden()

def public_repositories_view(request):
    repositories = Repository.objects.filter(visibility='public').order_by('-created_at')
    return render(request, 'public_repositories.html', {'repositories': repositories})


@login_required(login_url='login')
def my_repositories_view(request):
    repositories = Repository.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'my_repositories.html', {'repositories': repositories})


@login_required(login_url='login')
def create_repository_view(request):
    if request.method == 'POST':
        form = RepositoryCreateForm(request.POST, owner=request.user)
        if form.is_valid():
            form.save()
            return redirect('my-repositories')
    else:
        form = RepositoryCreateForm(owner=request.user)
    return render(request, 'create_repository.html', {'form': form})


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
            if request.user.role == 'superadmin':
                return redirect('superadmin-dashboard')
            elif request.user.role == 'admin':
                return redirect('admin-dashboard')
            else:
                return redirect('login-success')
    return render(request, 'force_password_change.html', {'error': error})