from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from visits.models import PageVisits
from django.conf import settings

LOGIN_URL = settings.LOGIN_URL

def home_view(request, *args, **kwargs):
    return about_view(request, *args,**kwargs)

def about_view(request, *args, **kwargs):
    total_qs = PageVisits.objects.all()
    qs = PageVisits.objects.filter(path=request.path)
    try:
        percent = (qs.count() * 100.0) / total_qs.count()
    except:
        percent = 0

    _html_template = "home.html"
    _page_title = "My Home Page!!!"
    _html_context = {
        "page_title":_page_title,
        "page_visit_count" : qs.count(),
        "percent" : percent,
        "total_page_visit" : total_qs.count()
        }
    PageVisits.objects.create(path=request.path)
    return render(request, _html_template, _html_context)

VALID_CODE = "abc123"

def pw_protected_view(request, *args, **kwargs):
    is_allowed = request.session.get('protected_page_allowed') or 0
    print(request.session.get('protected_page_allowed'), type(request.session.get('protected_page_allowed')))
    if request.method == "POST":
        user_pw_sent = request.POST.get("code") or None
        print("code:", user_pw_sent)
        if user_pw_sent == VALID_CODE:
            is_allowed = 1
            request.session['protected_page_allowed'] = is_allowed
    if is_allowed:
        return render(request, "protected/view.html", {})
    
    return render(request, "protected/entry.html", {})

@login_required(login_url=LOGIN_URL)
def user_only_view(request, *args, **kwargs):
    return render(request, "protected/user-only.html")

@staff_member_required(login_url=LOGIN_URL)
def staff_only_view(request, *args, **kwargs):
    return render(request, "protected/user-only.html")