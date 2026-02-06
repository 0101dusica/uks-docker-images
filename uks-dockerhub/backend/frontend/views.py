from django.shortcuts import render, redirect
from users.forms import CustomUserCreationForm, CustomLoginForm
from django.contrib.auth import login

def login_view(request):
    error = None
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                login(request, user)
                return redirect('login-success')
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
