
from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path("", views.profile_list_view, name='profile_list_view'),  
    path("<str:username>/", views.profile_detail_view, name='profile_detail_view'),  
]
