from django.contrib import admin
from .models import NOTAM_model, WeatherData

admin.site.register(NOTAM_model)
admin.site.register(WeatherData)
# Register your models here.
