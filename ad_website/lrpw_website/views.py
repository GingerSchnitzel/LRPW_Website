from django.shortcuts import render
from .extended_views.ad_schedule import scrape_notams
from django.http import JsonResponse
from datetime import date
from .models import NOTAM_model
from datetime import  timedelta


def fetch_notams(request):
    """
    Calls the NOTAM scraping function and displays the NOTAMs for today.
    """
    scrape_notams()  # Run the scraper to update NOTAMs in the database
    
    current_date = date.today() + timedelta(days=1)
    today = current_date.strftime("%y%m%d")
    notams = NOTAM_model.objects.filter(start_date__lte=today, end_date__gte=today)
    
    return render(request, 'notam_results.html', {'notams': notams})

def api_fetch_notams(request):
    """
    API endpoint to fetch NOTAMs in JSON format.
    """
    scrape_notams()  # Run the scraper to update NOTAMs in the database
    
    today = date.today().strftime("%y%m%d")
    notams = NOTAM_model.objects.filter(start_date__lte=today, end_date__gte=today)
    
    notam_list = list(notams.values())
    return JsonResponse({'notams': notam_list})