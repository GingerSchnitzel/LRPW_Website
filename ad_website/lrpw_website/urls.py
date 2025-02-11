from django.urls import path
from .views import fetch_notams, api_fetch_notams

urlpatterns = [
    path('notams/', fetch_notams, name='fetch_notams'),
    path('api/notams/', api_fetch_notams, name='api_fetch_notams'),
]
