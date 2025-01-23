import re
from datetime import datetime, timedelta
from typing import List
from tokenizer import Day, get_day

def get_next_day_name(current_day_name):
    # Map of day names to get the next day
    day_map = {
        "MON": "TUE", "TUE": "WED", "WED": "THU", "THU": "FRI", "FRI": "SAT", "SAT": "SUN", "SUN": "MON"
    }
    return day_map.get(current_day_name)

def parse_date_from_yyyymmdd(date_str: str) -> datetime:
    return datetime.strptime(date_str, '%y%m%d')

def get_weekday_date(start_date: datetime, weekday: Day, assigned_dates: set) -> datetime:
    """Get the next weekday date from a given start_date, ensuring that the date is not repeated."""
    days_ahead = weekday.value - 1 - start_date.weekday()  # Adjust for Python's weekday starting at 0 (Monday)
    if days_ahead < 0:
        days_ahead += 7
    
    current_date = start_date + timedelta(days=days_ahead)

    # Keep moving to the next week if the date has already been assigned
    while current_date in assigned_dates:
        current_date += timedelta(weeks=1)

    # Mark this date as assigned
    assigned_dates.add(current_date)
    
    return current_date

def format_date(date: datetime) -> str:
    return date.strftime('%a, %d %b %Y').upper()

def process_weekdays_with_dates(start_date: str, end_date: str, notam_data: List[str]) -> List[str]:
    start_date = parse_date_from_yyyymmdd(start_date)
    end_date = parse_date_from_yyyymmdd(end_date)
    
    notam_data_with_dates = []
    current_date = None

    i = 0
    while i < len(notam_data):
        day_entry = notam_data[i]  # This is a list: [day, [time_ranges]]
        day_token = day_entry[0]   # The day (e.g., "FRI", "TUE, 14 JAN 2025")
        time_ranges = day_entry[1]  # The list of time ranges (e.g., ["0800-1500", "1600-1900"])
        pattern = r'\b(MON|TUE|WED|THU|FRI|SAT|SUN)\b'
        match = re.search(pattern, day_token)
        found_day = match.group(0)
        day_enum = get_day(found_day)
        assigned_dates = set()
        
        if day_enum != Day.INVALID:  # If the token is a valid weekday
            # If the day token is a date (e.g., "TUE, 14 JAN 2025")
            if ',' in day_token:  # It contains a full date
                current_date = datetime.strptime(day_token, "%a, %d %b %Y")
            else:
                # Compute the date for the weekday if it's just a weekday without a date
                current_date = get_weekday_date(start_date, day_enum, assigned_dates)

            # Check if the current_date falls within the start_date and end_date
            if current_date and start_date <= current_date <= end_date:
                # Add the day and its corresponding formatted date
                #notam_data_with_dates.append(day_token)  # The weekday name or full date
                notam_data_with_dates.append(format_date(current_date))  # The formatted date string
                
                # Add the time ranges associated with this day
                for time_range in time_ranges:
                    notam_data_with_dates.append(time_range)

        i += 1  # Move to the next entry in notam_data
    
    return notam_data_with_dates

