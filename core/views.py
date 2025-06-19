from django.shortcuts import render
from .forms import SignUpForm
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import redirect
# Create your views here.


def home(request):
    return render(request, 'core/home.html')

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, "Account created successfully! Please set up your GitHub configuration.")
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'repository/signup.html', {'form': form})

