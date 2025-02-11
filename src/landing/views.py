from django.shortcuts import render
from visits.models import PageVisits
import helpers.numbers

# Create your views here.
from dashboard.views import dashboard_view

def landing_dashboard_page_view(request):
    if request.user.is_authenticated:
        return dashboard_view(request)
    total_qs = PageVisits.objects.all()
    PageVisits.objects.create(path=request.path)
    page_views_formatted = helpers.numbers.shorten_number(total_qs.count())
    social_views_formatted = helpers.numbers.shorten_number(total_qs.count())
    return render(request, "landing/main.html", {
        "page_view_count": page_views_formatted,
        "social_view_count": social_views_formatted
    })
