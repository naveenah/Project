from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

# Create your views here.
def login_view(request):
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
    return render(request, "auth/register.html", {})
