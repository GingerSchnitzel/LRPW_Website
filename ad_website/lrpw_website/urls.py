from django.urls import path
from .views import fetch_notams, api_fetch_notams, fetch_notams_for_week

urlpatterns = [
    path('notams/', fetch_notams, name='fetch_notams'),
    path('notams-week/', fetch_notams_for_week, name='notams_week'),
    path('api/notams/', api_fetch_notams, name='api_fetch_notams'),
]
