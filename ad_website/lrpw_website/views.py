from django.shortcuts import render
from .ad_schedule import scrape_notams
import certifi

def notam_view(request):
    print("Calling scrape_notams...")
    notam_data = scrape_notams()
    print("NOTAM Data:", notam_data)

    # Ensure a valid response for the template
    if not notam_data:
        notam_data = {'message': 'Unable to retrieve NOTAM data.'}

    return render(request, 'notam_results.html', {'notam_data': notam_data})

