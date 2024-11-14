from django.http import HttpResponse
from django.shortcuts import render
from visits.models import PageVisits

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