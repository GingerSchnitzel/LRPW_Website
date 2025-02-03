import requests
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import re
from NOTAM_process_functions.token_processor_dates import get_next_day_name
from NOTAM_process_functions.parse_NOTAM_content import parse_NOTAM_content


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
                                    NOTAM_schedule = parse_NOTAM_content(NOTAM_start_date, NOTAM_end_date,content)

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
                                        NOTAM_schedule =  parse_NOTAM_content(NOTAM_start_date, NOTAM_end_date,content)
                                    
            
                                #print(f"Content: {content}")
                                print(f"NOTAM_purpose: {NOTAM_purpose}")
                        except Exception as e:
                                    print(f"Error processing section {identifier}: {e}")

                    if not NOTAM_purpose:
                        print("No schedule NOTAM available.")
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
 
 
