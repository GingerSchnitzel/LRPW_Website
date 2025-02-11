import pytz
from datetime import datetime

def convert_schedule_to_eet(schedule):
    # Define timezones
    utc = pytz.utc
    eet = pytz.timezone("Europe/Bucharest")

    # Process schedule
    converted_schedule = []
    i = 0

    while i < len(schedule):
        date_str = schedule[i]
        i += 1
        time_ranges = []

        # Collect all time ranges for the same date
        while i < len(schedule) and schedule[i] != "CLSD" and not schedule[i].startswith(tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")):
            time_ranges.append(schedule[i])
            i += 1

        if not time_ranges:  # If no time ranges found (e.g., "CLSD" case), skip
            continue  

        # Parse date
        date_obj = datetime.strptime(date_str, "%a, %d %b %Y")
        formatted_date = date_obj.strftime("%a, %d.%m.%Y")  # Fixed-length format

        eet_time_ranges = []
        for time_range in time_ranges:
            # Extract start and end time
            start_time = datetime.strptime(time_range[:4], "%H%M").time()
            end_time = datetime.strptime(time_range[5:], "%H%M").time()

            # Convert to EET
            start_dt = datetime.combine(date_obj, start_time, utc).astimezone(eet)
            end_dt = datetime.combine(date_obj, end_time, utc).astimezone(eet)

            # Store formatted time range
            eet_time_ranges.append(f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}")

        # Join multiple time ranges into one row
        converted_schedule.append(f"{formatted_date} {', '.join(eet_time_ranges)}")

    return converted_schedule
