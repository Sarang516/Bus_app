"""
bts_project/urls.py  –  Root URL configuration
"""
from django.urls import path, include

urlpatterns = [
    path("", include("api.urls")),
]
