import requests
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import re
from enum import Enum
from typing import List, Tuple, Optional


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
    days_times = {}


class TokenType(Enum):
    DAY = 1
    DASH = 2
    TIME_RANGE = 3
    CLSD = 4
    DATE = 5
    INVALID = 6

class Day(Enum):
    MON = 1
    TUE = 2
    WED = 3
    THU = 4
    FRI = 5
    SAT = 6
    SUN = 7
    INVALID = 8

# Helper Functions
def make_day_range(start: Day, end: Day) -> List[Day]:
    if start == Day.INVALID or end == Day.INVALID:
        return []
    
    # Handle the case when start day is after end day (e.g., MON - THU)
    if start.value <= end.value:
        return [Day(day) for day in range(start.value, end.value + 1)]
    else:
        return []

def get_day(token: str) -> Day:
    days_map = {
        "MON": Day.MON,
        "TUE": Day.TUE,
        "WED": Day.WED,
        "THU": Day.THU,
        "FRI": Day.FRI,
        "SAT": Day.SAT,
        "SUN": Day.SUN,
    }
    return days_map.get(token.upper(), Day.INVALID)

def is_time_range(token: str) -> bool:
    return bool(re.match(r"^(\d{4})-(\d{4})$", token))

def is_date(token: str) -> bool:
    return bool(re.match(r"^\d{2} \w{3}( \d{4})?$", token))  # Matches formats like "06 NOV" or "06 NOV 2020"

def parse_date(token: str) -> Optional[datetime]:
    try:
        current_year = datetime.now().year  # Get the current year
        if len(token.split()) == 2:  # Format: "06 NOV"
            return datetime.strptime(f"{token} {current_year}", "%d %b %Y")
        elif len(token.split()) == 3:  # Format: "06 NOV 2020"
            return datetime.strptime(token, "%d %b %Y")
        return None
    except ValueError:
        return None

def get_type(token: str) -> TokenType:
    if get_day(token) != Day.INVALID:
        return TokenType.DAY
    elif token == "-":
        return TokenType.DASH
    elif is_time_range(token):
        return TokenType.TIME_RANGE
    elif token.upper() == "CLSD":
        return TokenType.CLSD
    elif is_date(token):
        return TokenType.DATE
    else:
        return TokenType.INVALID

def generate_date_range(start_date: datetime, end_date: datetime) -> List[datetime]:
    """Generates all dates between start_date and end_date inclusive."""
    delta = end_date - start_date
    return [start_date + timedelta(days=i) for i in range(delta.days + 1)]

# Parsing Functions
def get_time_groups(tokens: List[str]) -> List[Tuple[List[datetime], List[str]]]:
    class State(Enum):
        START = 1
        GOT_DAY = 2
        GOT_DASH = 3
        GOT_TIME_RANGE = 4
        GOT_DATE = 5

    state = State.START
    current_dates = []
    current_time_ranges = []
    time_groups = []

    for token in tokens:
        token_type = get_type(token)

        if state == State.START:
            if token_type == TokenType.DAY:
                current_dates.append(get_day(token))
                state = State.GOT_DAY
            elif token_type == TokenType.DATE:
                current_dates.append(parse_date(token))
                state = State.GOT_DATE
            else:
                raise ValueError(f"Unexpected token at start: {token}")

        elif state == State.GOT_DATE:
            if token_type == TokenType.DAY:
                current_dates.append(get_day(token))
                state = State.GOT_DAY
            elif token_type in [TokenType.TIME_RANGE, TokenType.CLSD]:
                current_time_ranges.append(token)
                state = State.GOT_TIME_RANGE
            elif token_type == TokenType.DASH:
                state = State.GOT_DASH
            else:
                raise ValueError(f"Unexpected token after date: {token}")

        elif state == State.GOT_DAY:
            if token_type == TokenType.DAY:
                current_dates.append(get_day(token))
            elif token_type == TokenType.DASH:
                state = State.GOT_DASH
            elif token_type in [TokenType.TIME_RANGE, TokenType.CLSD]:
                current_time_ranges.append(token)
                state = State.GOT_TIME_RANGE
            elif token_type == TokenType.DATE:
                current_dates.append(parse_date(token))
                state = State.GOT_DATE
            else:
                raise ValueError(f"Unexpected token after day: {token}")

        elif state == State.GOT_DASH:
            if token_type == TokenType.DAY:
                # Handle dash between days
                start_day = current_dates[-1]
                end_day = get_day(token)
                day_range = make_day_range(start_day, end_day)
                current_dates.extend(day_range)
                state = State.GOT_DAY
            elif token_type == TokenType.DATE:
                # Handle dash between dates
                start_date = current_dates[-1]
                end_date = parse_date(token)
                date_range = generate_date_range(start_date, end_date)
                current_dates.extend(date_range)
                state = State.GOT_DATE
            else:
                raise ValueError(f"Unexpected token after dash: {token}")

        elif state == State.GOT_TIME_RANGE:
            if token_type in [TokenType.TIME_RANGE, TokenType.CLSD]:
                current_time_ranges.append(token)
            elif token_type == TokenType.DATE:
                time_groups.append((current_dates, current_time_ranges))
                current_dates = [parse_date(token)]
                current_time_ranges = []
                state = State.GOT_DATE
            elif token_type == TokenType.DAY:
                time_groups.append((current_dates, current_time_ranges))
                current_dates = [get_day(token)]
                current_time_ranges = []
                state = State.GOT_DAY
            else:
                raise ValueError(f"Unexpected token after time range: {token}")

    if current_dates and current_time_ranges:
        time_groups.append((current_dates, current_time_ranges))

    return time_groups

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

                elif isinstance(date, datetime):
                    # Full date available, format it
                    day_date = date.strftime('%a, %d %b %Y').upper()

                    # Remove any existing entry for the corresponding day-only entry with the same time range
                    notam_data = [
                        (d, t) for d, t in notam_data
                        if not (d.startswith(date.strftime('%a').upper()) and t == time_ranges)
                    ]

                    # Add the full date entry
                    notam_data.append((day_date, time_ranges))

        # Print the processed data
        for date, times in notam_data:
            print(f"{date}: {', '.join(times)}")

    except ValueError as e:
        print("Error:", e)
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

"""
    Parses the D) or E) sections of a NOTAM to extract day and time ranges.
"""
def associate_day_time_ranges(content):
    try:
        # Extract day ranges and time intervals using regex
       
        day_time_pattern = r"(?:MON|TUE|WED|THU|FRI|SAT|SUN)(?:-(?:MON|TUE|WED|THU|FRI|SAT|SUN))?|(?:\d{4}-\d{4}|CLSD)"
        matches = re.findall(day_time_pattern, content)
        # Handle case where no valid day-time patterns are found
        if not matches:
            raise ValueError("No valid day-time patterns found in the content.")

        try:
            time_groups = get_time_groups(matches)
            for days, time_ranges in time_groups:
                NOTAM.days_times.append()

        except ValueError as e:
            print("Error:", e)
            
    except ValueError as e:
        print(f"ValueError: {e}")
        NOTAM_days_times = {}  # Return an empty dictionary on error
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        NOTAM_days_times = {}  # Return an empty dictionary on error

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
        formatted_date = current_date.strftime("%y%m%d")  # Format the date as YYMMDD
        current_day = datetime.now().strftime("%a").upper()  # Get the current day of the week as a three-letter abbreviation eg. SAT
        print(f"Formatted date: {formatted_date}")
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
                    NOTAM_days_times = {}
                    
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
                            if identifier == 'D' and not NOTAM_days_times:
                                if content.strip():  # Check if the D) section has content
                                    print(f"Parsing D) section: {content}")
                                    NOTAM_days_times = parse_NOTAM_schedule(content)
                                else:
                                    print("D) section exists but is empty.")

                            # Extract purpose of the NOTAM (E) section) and schedule
                            if identifier == 'E' and NOTAM_purpose is None:
                                NOTAM_section_E = content.strip()
                                if NOTAM.AD_CLOSED in NOTAM_section_E:
                                    NOTAM_purpose = NOTAM.AD_CLOSED
                                elif NOTAM.AD_OPEN in NOTAM_section_E:
                                    NOTAM_purpose = NOTAM.AD_OPEN
                                    if not NOTAM_days_times:
                                        NOTAM_days_times = parse_NOTAM_schedule(content)
            
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
                        break

                    elif NOTAM_start_date and NOTAM_end_date and NOTAM_purpose:
                        if NOTAM_start_date <= formatted_date <= NOTAM_end_date:
                            if NOTAM_days_times:
                                if current_day in NOTAM_days_times:
                                    print("Valid NOTAM found:", notam_text)
                                    return {
                                    'notam_text': notam_text,
                                    'purpose': NOTAM_purpose,
                                    'start_date': NOTAM_start_date,
                                    'start_hour': NOTAM_start_hour,
                                    'end_date': NOTAM_end_date,
                                    'end_hour': NOTAM_end_hour,
                                    'schedule': NOTAM_days_times[current_day],
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
 
 
