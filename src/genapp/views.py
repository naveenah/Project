from django.http import HttpResponse
from django.shortcuts import render
from visits.models import PageVisits

def home_view(request, *args, **kwargs):
    total_qs = PageVisits.objects.all()
    qs = PageVisits.objects.filter(path=request.path)
    _html_template = "home.html"
    _page_title = "My Home Page!!!"
    _html_context = {
        "page_title":_page_title,
        "page_visit_count" : qs.count(),
        "total_page_visit" : total_qs.count()
        }
    PageVisits.objects.create(path=request.path)
    return render(request, _html_template, _html_context)