import re
from .token_processor_days import process_tokens
from .token_processor_dates import process_weekdays_with_dates

def parse_NOTAM_contents(start_date, end_date, content):
    """
    Parses NOTAM content to extract day, date, and time ranges.

    Args:
        content (str): The NOTAM content to parse.

    Returns:
        list: A list of extracted schedules in a structured format.
              Returns an empty list if parsing fails.
    """
    try:
        # Regex pattern to match day ranges, dates, and time intervals
        day_time_pattern = (
            r'((?:MON|TUE|WED|THU|FRI|SAT|SUN))\s*,?\s*(\d{1,2}\s*'  # Day of the week followed by a date
            r'(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*'  # Month abbreviation
            r'(?:\d{4}(?!-\d{4}))?)|'  # Optional 4-digit year (not followed by a range)
            r'(\d{1,2}\s*(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*'  # Date format with month abbreviation
            r'(?:\d{4}(?!-\d{4}))?)|'  # Optional 4-digit year (not followed by a range)
            r'((?:MON|TUE|WED|THU|FRI|SAT|SUN))|'  # Day of the week
            r'(\d{4}-\d{4})|'  # Time range format (e.g., 0800-1500)
            r'(CLSD)|'  # CLSD keyword
            r'(-)'  # Dash

        )

        # # Use re.finditer to match groups and extract each string individually
        matches = re.finditer(day_time_pattern, content)

      # Extract each matched string from the groups
        filtered_matches = []
        for match in matches:
            for group in match.groups():
                if group:
                    filtered_matches.append(group)
      
        if not filtered_matches:
            raise ValueError("No valid day-time patterns found in the content.")

        # Process matches to extract structured schedule
        extracted_schedule = process_tokens(filtered_matches, start_date, end_date)  
        processed_schedule = process_weekdays_with_dates(extracted_schedule, start_date, end_date)
        # Return the structured schedule
        return processed_schedule

    except ValueError as ve:
        print(f"ValueError: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    # Return an empty list on error
    return []
