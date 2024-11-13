from django.http import HttpResponse
from django.shortcuts import render

def home_page_view(request, *args, **kwargs):
    _html_template = "home.html"
    _page_title = "My Home Page!!!"
    _html_context = {"page_title":_page_title}
    return render(request, _html_template, _html_context)