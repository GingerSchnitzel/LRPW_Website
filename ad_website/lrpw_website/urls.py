from django.urls import path
from .views import notam_view# Import your view

urlpatterns = [
    path('scrape/', notam_view, name='scrape_notams'),  # Add the URL pattern
]
