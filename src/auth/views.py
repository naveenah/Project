from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

# Create your views here.
def login_view(request):
    """
    Handles user login.

    If the request method is POST, it authenticates the user and logs them in
    if the credentials are valid. Otherwise, it displays the login form.
    """
    if request.method == "POST":
        username = request.POST.get("username") or None
        password = request.POST.get("password") or None

        if all([username, password]):
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")

    return render(request, "auth/login.html", {})

def register_view(request):
    """
    Displays the registration page.
    """
    return render(request, "auth/register.html", {})
