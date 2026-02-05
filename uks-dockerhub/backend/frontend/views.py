from django.shortcuts import render, redirect
from users.forms import CustomUserCreationForm

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
