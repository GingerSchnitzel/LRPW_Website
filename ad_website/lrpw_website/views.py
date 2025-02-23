from django.shortcuts import render
from .extended_views.ad_schedule import scrape_notams
from .extended_views.default_schedule import get_default_schedule
from django.http import JsonResponse
from datetime import date
from .models import NOTAM_model
from datetime import  timedelta

def api_fetch_notams(request):
    """
    API endpoint to fetch NOTAMs in JSON format.
    """
    scrape_notams()  # Run the scraper to update NOTAMs in the database
    
    today = date.today().strftime("%y%m%d")
    notams = NOTAM_model.objects.filter(start_date__lte=today, end_date__gte=today)
    
    notam_list = list(notams.values())
    return JsonResponse({'notams': notam_list})

def fetch_notams(request, target_date=None):
    """
    Calls the NOTAM scraping function and displays the NOTAMs for the specified or today's date.
    """
    if target_date:
        current_date = target_date
    else:
        current_date = date.today()
    
    today = current_date.strftime("%y%m%d")
    
    # Run the scraper to update NOTAMs in the database
    scrape_notams()
    
    # Get NOTAMs that are valid for the specified or today's date
    notams = NOTAM_model.objects.filter(start_date__lte=today, end_date__gte=today)
    
    # Group NOTAMs by start_date and end_date
    unique_notams = {}
    
    for notam in notams:
        key = (notam.start_date, notam.end_date)
        
        if key in unique_notams:
            existing_notam = unique_notams[key]
            
            if notam.year > existing_notam.year or (notam.year == existing_notam.year and notam.number > existing_notam.number):
                existing_notam.replaced = True
                existing_notam.replaced_by = notam
                existing_notam.save()
                
                unique_notams[key] = notam
            elif notam.year == existing_notam.year and notam.number != existing_notam.number:
                existing_notam.display_schedule = merge_schedules(existing_notam.schedule, notam.schedule)
                existing_notam.display_schedule_updated = True
        else:
            unique_notams[key] = notam
    
    notams_to_display = list(unique_notams.values())
    
    # Get the default aerodrome schedule if no relevant NOTAMs are available
    schedule = get_default_schedule(notams)
    
    # Prepare the context for the template and pass the NOTAMs and schedule to display
    return render(request, 'notam_results.html', {
        'notams': notams_to_display,
        'schedule': schedule
    })

def fetch_notams_for_week(request):
    """
    Calls fetch_notams() for each day in the current week and collects results.
    """
    start_date = date.today()  # Start from today
    week_notams = {}

    for i in range(7):  # Loop through the next 7 days
        target_date = start_date + timedelta(days=i)
        response = fetch_notams(request, target_date)  # Call fetch_notams for the specific date
        week_notams[target_date.strftime("%y%m%d")] = response  # Store results by date

    return render(request, 'notam_week_results.html', {'week_notams': week_notams})

def merge_schedules(existing_schedule, new_schedule):
    """
    Merge the new schedule with the existing schedule.
    If a day in the new schedule exists in the old schedule, replace it.
    """
    # If no existing schedule, return the new schedule
    if not existing_schedule:
        return new_schedule
    
    # Create a set for faster lookup, extracting the date part from each schedule entry
    existing_dates = set(entry.split(' ')[0] for entry in existing_schedule)  # Assuming the first part is the date (e.g., "Mon, 17.02.2025")
    
    merged_schedule = []

    # Loop over the new entries
    for new_entry in new_schedule:
        date_part = new_entry.split(' ')[0]  # Extract the date part (e.g., "Mon, 17.02.2025")
        
        # If the date is already in the existing schedule, update it
        if date_part in existing_dates:
            # Find the corresponding entry in the existing schedule and replace it
            for i, existing_entry in enumerate(existing_schedule):
                if existing_entry.split(' ')[0] == date_part:
                    existing_schedule[i] = new_entry  # Replace the old schedule for this date
                    break
        else:
            # If the date doesn't exist in the existing schedule, add it
            merged_schedule.append(new_entry)
    
    # Add any entries from the existing schedule that were not replaced
    merged_schedule.extend(existing_schedule)
    
    return merged_schedule  # Return the merged schedule as a list of strings

