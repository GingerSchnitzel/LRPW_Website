from django.urls import path
from .views import fetch_notams, api_fetch_notams, fetch_notams_for_week, map_view, weather_api, weather_view

urlpatterns = [
    path('notams/', fetch_notams, name='fetch_notams'),
    path('notams-week/', fetch_notams_for_week, name='notams_week'),
    path('api/notams/', api_fetch_notams, name='api_fetch_notams'),
    path("map/", map_view, name="map"),
    path('weather/', weather_view, name='weather_view'),  # Renders the HTML template
    path('api/weather/', weather_api, name='weather_api'),  # Returns JSON data
]
