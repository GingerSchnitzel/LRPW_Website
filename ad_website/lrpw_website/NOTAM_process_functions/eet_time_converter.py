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
        while i < len(schedule) and schedule[i][:3] not in ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]:
            time_ranges.append(schedule[i])
            i += 1

        # Parse date
        date_obj = datetime.strptime(date_str.title(), "%a, %d %b %Y")
        formatted_date = date_obj.strftime("%a, %d.%m.%Y").capitalize()  # Capitalize the first letter of the weekday

        # Process time ranges and convert to EET
        eet_entry = [formatted_date]
        for time_range in time_ranges:
            if time_range == "CLSD":
                eet_entry.append("CLSD")
            else:
                # Extract start and end time
                start_time = datetime.strptime(time_range[:4], "%H%M").time()
                end_time = datetime.strptime(time_range[5:], "%H%M").time()

                # Convert to EET
                start_dt = datetime.combine(date_obj, start_time, utc).astimezone(eet)
                end_dt = datetime.combine(date_obj, end_time, utc).astimezone(eet)

                # Add converted time range as a separate element
                eet_entry.append(f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}")

        # Add the formatted entry to the final result
        converted_schedule.append(eet_entry)

    return converted_schedule
