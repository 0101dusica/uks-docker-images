from users.permissions import superadmin_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from users.permissions import admin_required, superadmin_required
from users.models import User
from django.shortcuts import render, redirect
from users.forms import CustomUserCreationForm, CustomLoginForm
from django.contrib.auth import login

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
        form = CustomLoginForm()
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
    return render(request, 'superadmin_dashboard.html', {'users': users, 'admins': admins})

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