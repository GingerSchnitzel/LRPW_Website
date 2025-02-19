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

def fetch_notams(request):
    """
    Calls the NOTAM scraping function and displays the NOTAMs for today.
    """
    scrape_notams()  # Run the scraper to update NOTAMs in the database
    
    current_date = date.today()
    today = current_date.strftime("%y%m%d")
    
    # Get NOTAMs that are valid today
    notams = NOTAM_model.objects.filter(start_date__lte=today, end_date__gte=today)
    
    # Group NOTAMs by start_date and end_date
    unique_notams = {}
    
    for notam in notams:
        # Key for grouping NOTAMs by start and end date
        key = (notam.start_date, notam.end_date)
        
        # If this key already exists, compare and handle the logic
        if key in unique_notams:
            existing_notam = unique_notams[key]
            
            # Case 1: The entire NOTAM is replaced (same dates, newer NOTAM)
            if notam.year > existing_notam.year or (notam.year == existing_notam.year and notam.number > existing_notam.number):
                # Mark the older NOTAM as replaced
                existing_notam.replaced = True
                existing_notam.replaced_by = notam
                existing_notam.save()
                
                # Replace the old NOTAM with the new one in the dictionary
                unique_notams[key] = notam
            
            # Case 2: Only a part of the schedule is modified (same dates, schedule changed)
            elif notam.year == existing_notam.year and notam.number != existing_notam.number:
                # Update the displayed schedule for the affected days (only modify display, no DB changes)
                existing_notam.display_schedule = merge_schedules(existing_notam.schedule, notam.schedule)
                existing_notam.display_schedule_updated = True  # Mark to indicate that it was updated
        else:
            # If this key does not exist, add the NOTAM to the dictionary
            unique_notams[key] = notam
    
    # The dictionary now contains only the most recent NOTAMs for each (start_date, end_date) group
    notams_to_display = list(unique_notams.values())
    
    # Get the default aerodrome schedule in no other NOTAMs are available
    schedule = get_default_schedule(notams)
    
    # Prepare the context for the template and pass the NOTAMs and schedule to display
    return render(request, 'notam_results.html', {
        'notams': notams_to_display,
        'schedule': schedule  # Add the schedule to the context
    })

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

