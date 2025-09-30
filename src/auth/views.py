from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.
def login_view(request):
    """
    Handles user login.

    If the request method is POST, it authenticates the user and logs them in
    if the credentials are valid. Otherwise, it displays the login form.
    """
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            try:
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect("/")
            except Exception as e:
                # Log the exception e
                form.add_error(None, "An unexpected error occurred during authentication.")
    else:
        form = AuthenticationForm()
    return render(request, "auth/login.html", {"form": form})

def register_view(request):
    """
    Displays the registration page.
    """
    return render(request, "auth/register.html", {})
