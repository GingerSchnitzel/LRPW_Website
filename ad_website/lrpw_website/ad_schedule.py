import requests
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from enum import Enum
from typing import List, Tuple, Optional
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import re



class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("AES128-SHA256")
        kwargs["ssl_context"] = ctx
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)

class NOTAM:
    URL = 'https://flightplan.romatsa.ro/init/notam/getnotamlist?ad=LRPW'
    AD_CLOSED = 'AD CLSD'
    AD_OPEN = 'TEMPORARY CHANGE OF AD ADMINISTRATION OPS HOURS'
    SERIES_A = 'A'
    MAGIC_WORD = '/init/notam/getnotam'


def process_tokens(tokens: List[str]):
    notam_data = []

    try:
        time_groups = get_time_groups(tokens)

        for days, time_ranges in time_groups:
            for date in days:
                if isinstance(date, Day):
                    # Only day name, format it
                    date_str = date.name  # Get the name of the enum (e.g., "MON", "FRI")

                    # Only add day name if no full date entry exists already
                    if not any(d.startswith(date_str) for d, t in notam_data):
                        notam_data.append((date_str, time_ranges))
                    continue
                elif ',' in date:
                    # Full date available, format it again for safety
                    date_str = date

                    # Remove any existing entry for the corresponding day-only entry with the same time range
                    notam_data = [
                        (d, t) for d, t in notam_data
                        if not (d == date_str[:3] and t == time_ranges)
                    ]
                '''   
                elif isinstance(date, datetime):
                    day_date = date.strftime('%a, %d %b %Y').upper()

                    # Remove any existing entry for the corresponding day-only entry with the same time range
                    notam_data = [
                        (d, t) for d, t in notam_data
                        if not (d == date_str and t == time_ranges)
                    ]
                '''   
                # Add the full date entry
                notam_data.append((date_str, time_ranges))
        
        # Return the processed data
        return notam_data

    except ValueError as e:
        print("Error:", e)
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []
'''     
# Example Usage
tokens1 = ["FRI", "10 JAN", "0800-1500", "SAT", "11 JAN 2025", "CLSD"]
tokens2 = ["TUE", "0800-1500", "WED", "CLSD"]  # no date
tokens3 = ["FRI", "10 JAN 2025", "0800-1500", "SAT", "11 JAN", "CLSD"]  # mix of dates with and without year
tokens4 = ["MON", "TUE", "-", "THU", "0900-1700"]  # dash between days
tokens5 = ["10 JAN 2024", "-", "14 JAN 2024", "0800-1500", "1600-1700"]
tokens6 = ["10 JAN", "0800-1500"]
tokens7 = ["20 JAN", "-", "25 JAN", "0800-1500"]

process_tokens(tokens1)
process_tokens(tokens2)
process_tokens(tokens3)
process_tokens(tokens4)
process_tokens(tokens5)
process_tokens(tokens6)
process_tokens(tokens7)
'''

def get_next_day_name(current_day_name):
    # Map of day names to get the next day
    day_map = {
        "MON": "TUE", "TUE": "WED", "WED": "THU", "THU": "FRI", "FRI": "SAT", "SAT": "SUN", "SUN": "MON"
    }
    return day_map.get(current_day_name)

def parse_date_from_yyyymmdd(date_str: str) -> datetime:
    return datetime.strptime(date_str, '%y%m%d')

def get_weekday_date(start_date: datetime, weekday: Day) -> datetime:
    """Get the next weekday date from a given start_date."""
    days_ahead = weekday.value - 1 - start_date.weekday()  # Adjust for Python's weekday starting at 0 (Monday)
    if days_ahead < 0:
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)

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
        
        if day_enum != Day.INVALID:  # If the token is a valid weekday
            # If the day token is a date (e.g., "TUE, 14 JAN 2025")
            if ',' in day_token:  # It contains a full date
                current_date = datetime.strptime(day_token, "%a, %d %b %Y")
            else:
                # Compute the date for the weekday if it's just a weekday without a date
                current_date = get_weekday_date(start_date, day_enum)

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


def parse_NOTAM_content(start_date, end_date, content):
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
        extracted_schedule = process_tokens(filtered_matches)  
        processed_schedule = process_weekdays_with_dates(start_date, end_date,extracted_schedule)
        # Return the structured schedule
        return processed_schedule

    except ValueError as ve:
        print(f"ValueError: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    # Return an empty list on error
    return []

"""
    Scrapes NOTAMs from the specified URL and extracts details for relevant NOTAMs.
"""
def scrape_notams(NOTAMS_URL = NOTAM.URL):

    try:
        # Send the request and parse the response with BeautifulSoup
        #headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'}
        print("Sending request to:", NOTAMS_URL)

        session = requests.Session()
        session.mount("https://", TLSAdapter())

        certificate_path = './certificates/cert.pem'

        #Send the GET request
        response = session.get(NOTAMS_URL, verify=certificate_path)
        print(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            return {'message': f"Failed to fetch NOTAMs. Status code: {response.status_code}"}
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # Get the current date
        print("Parsing response content.")
        current_date = date.today()
        YYMMDD_date = current_date.strftime("%y%m%d")  # Format the date as YYMMDD
        long_date = current_date.strftime("%d %b %Y").upper() # Format the full date as "15 SEP 2024"
        short_date = current_date.strftime("%d %b").upper() # Format the short date as "15 SEP"

        
        current_day = datetime.now().strftime("%a").upper()  # Get the current day of the week as a three-letter abbreviation eg. SAT
        next_day = get_next_day_name(current_day) # Get the next day of the week as a three-letter abbreviation eg. SAT
        print(f"Formatted date: {YYMMDD_date}")
        print(f"Current day of week: {current_day}")

        # Iterate over all the NOTAMs on the page
        for notam_entry in soup.find_all("div", style="font-family:monospace; font-size:large;"):
            
            notam_decoded = notam_entry.decode_contents().strip()
            #print(f"Notam decoded: {notam_decoded}")
            # Remove any XML declaration dynamically using a regex
            notam_decoded = re.sub(r'<\?xml .*?\?>', '', notam_decoded).strip()
            # Debugging: Print the decoded NOTAM
            print(f"NOTAM Decoded after stripping XML: {notam_decoded}")

            if NOTAM.MAGIC_WORD in notam_decoded:
                print(f"Processing NOTAM decoded: {notam_decoded}")
              
                notam_soup = BeautifulSoup(notam_decoded, 'html.parser')
                notam_text = notam_soup.get_text(separator=' ', strip=True).strip("()").strip()
                print(f"NOTAM text: {notam_text}")
                #print(f"NOTAM starts with: {notam_text[0]}")
                if notam_text.startswith(NOTAM.SERIES_A):  # Check if the NOTAM starts with 'A'
                    
                    match = re.match(r'^A\d{4}/\d{2}', notam_text)
                    if match:
                        NOTAM_series = str(match.group(0))
                        print(f"NOTAM series: {NOTAM_series}")
                        NOTAM_number = int(NOTAM_series[1:5])
                        print(f"NOTAM number: {NOTAM_number}")
                    else:
                        print("No valid NOTAM series match found. Skipping this NOTAM.")
                        continue

                    NOTAM_purpose = None
                    NOTAM_start_date = None
                    NOTAM_end_date = None
                    NOTAM_start_hour = None
                    NOTAM_end_hour = None
                    NOTAM_schedule = []
                    NOTAM_current_and_next_day_schedule = {}
                    
                    #Regular expression to match section identifiers and their content
                    section_pattern = r'([A-Z])\)\s*(.*?)(?=(?: [A-Z]\)|$))'
                    # Split the NOTAM text into sections
                    sections = re.findall(section_pattern, notam_text)
                    # Extract the details of the NOTAM
                    if not sections:
                        print(f"Failed to extract sections from NOTAM: {notam_text}")
                        continue

                    print(f"Extracted sections: {sections}")

                      # Iterate over the extracted sections
                    for identifier, content in sections:
                        try:
                        # Extract the start date (B) section)
                            if identifier == 'B' and NOTAM_start_date is None:
                                #print(f"Content: {content}")
                                NOTAM_start_date = content.strip()[:6]  # Assuming the date is in YYMMDDhhmm format
                                NOTAM_start_hour = content.strip()[6:]
                                print(f"NOTAM_start_date: {NOTAM_start_date}")
                                print(f"NOTAM_start_hour: {NOTAM_start_hour}")

                            # Extract the end date (C) section)
                            if identifier == 'C' and NOTAM_end_date is None:
                                NOTAM_end_date = content.strip()[:6]  # Assuming the date is in YYMMDDhhmm format
                                NOTAM_end_hour = content.strip()[6:]
                                print(f"NOTAM_end_date: {NOTAM_end_date}")
                                print(f"NOTAM_end_hour: {NOTAM_end_hour}")

                            # Extract the schedule IF a/d closed (D) section
                            if identifier == 'D' and not NOTAM_schedule:
                                if content.strip():  # Check if the D) section has content
                                    print(f"Parsing D) section: {content}")
                                    NOTAM_schedule = parse_NOTAM_content(content)

                                else:
                                    print("D) section exists but is empty.")

                            # Extract purpose of the NOTAM (E) section) and schedule
                            if identifier == 'E' and NOTAM_purpose is None:
                                NOTAM_section_E = content.strip()
                                if NOTAM.AD_CLOSED in NOTAM_section_E:
                                    NOTAM_purpose = NOTAM.AD_CLOSED
                                elif NOTAM.AD_OPEN in NOTAM_section_E:
                                    NOTAM_purpose = NOTAM.AD_OPEN
                                if not NOTAM_schedule:
                                        NOTAM_schedule = parse_NOTAM_content(content)
                                    
            
                                #print(f"Content: {content}")
                                print(f"NOTAM_purpose: {NOTAM_purpose}")
                        except Exception as e:
                                    print(f"Error processing section {identifier}: {e}")

                    if not NOTAM_purpose:
                        print("Not schedule NOTAM.")
                        NOTAM_end_date = None
                        NOTAM_purpose = None
                        NOTAM_start_date = None
                        NOTAM_start_hour = None
                        NOTAM_end_hour = None
                        NOTAM_schedule = []
                        break

                    elif NOTAM_start_date and NOTAM_end_date and NOTAM_purpose:
                        if NOTAM_start_date <= YYMMDD_date <= NOTAM_end_date:
                            if NOTAM_purpose and NOTAM_schedule:
                                if current_day in NOTAM_schedule:
                                    print("Valid NOTAM found:", notam_text)
                                    return {
                                    'notam_text': notam_text,
                                    'purpose': NOTAM_purpose,
                                    'start_date': NOTAM_start_date,
                                    'start_hour': NOTAM_start_hour,
                                    'end_date': NOTAM_end_date,
                                    'end_hour': NOTAM_end_hour,
                                    'schedule': NOTAM_schedule,
                                    }
                            else:
                                print("Valid NOTAM found:", notam_text)
                                return {
                                'notam_text': notam_text,
                                'purpose': NOTAM_purpose,
                                'start_date': NOTAM_start_date,
                                'start_hour': NOTAM_start_hour,
                                'end_date': NOTAM_end_date,
                                'end_hour': NOTAM_end_hour,
                                }

        print("No valid NOTAMs found.")
        return {'message': 'No valid NOTAMs found for today.'}

    except Exception as e:
        print(f"An error occurred: {e}")
 
 
