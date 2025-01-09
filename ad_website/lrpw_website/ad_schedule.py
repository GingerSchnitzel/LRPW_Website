import requests
from bs4 import BeautifulSoup
from datetime import date, datetime
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
    PURPOSE_VARIATIONS = ['TEMPORARY CHANGE OF AD ADMINISTRATION OPS HOURS.', 
                          'TEMPORARY CHANGE OF AD ADMINISTRATION OPS HOURS', 
                          'TEMPORARY CHANGE OF AD ADMINISTRATION OPS HOURS .',
                          'AD CLSD']
    SERIES_A = 'A'
    MAGIC_WORD = '/init/notam/getnotam'
found_NOTAM = False

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
                    NOTAM_series = str(match.group(0))
                    print(f"NOTAM series: {NOTAM_series}")

                    NOTAM_number = int(NOTAM_series[1:5])
                    print(f"NOTAM number: {NOTAM_number}")

                    NOTAM_purpose = None
                    NOTAM_start_date = None
                    NOTAM_end_date = None
                    NOTAM_start_hour = None
                    NOTAM_end_hour = None
                    NOTAM_clsd_days_D = []
                    NOTAM_start_clsd_D = None
                    NOTAM_end_clsd_D = None


                    #Regular expression to match section identifiers and their content
                    section_pattern = r'([A-Z])\)\s*(.*?)(?=(?: [A-Z]\)|$))'
                    # Split the NOTAM text into sections
                    sections = re.findall(section_pattern, notam_text)
                    # Extract the details of the NOTAM
                  
                      # Iterate over the extracted sections
                    for identifier, content in sections:
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

                        # Inside your loop for sections
                        if identifier == 'D' and not NOTAM_clsd_days_D and NOTAM_start_clsd_D is None and NOTAM_end_clsd_D is None:
                            if content.strip():  # Check if the D) section has content
                                print(f"Parsing D) section: {content}")
                                
                                # Extract days before the first digit
                                days_match = re.match(r"([A-Z\- ]+)", content)
                                NOTAM_clsd_days_D = [day.strip() for day in days_match.group(1).split()] if days_match else []

                                # Extract start and end times
                                time_match = re.search(r"(\d{4})-(\d{4})", content)
                                if time_match:
                                    NOTAM_start_clsd_D = time_match.group(1)
                                    NOTAM_end_clsd_D = time_match.group(2)
                                
                                # Debug output
                                print(f"NOTAM_clsd_days_D: {NOTAM_clsd_days_D}")
                                print(f"NOTAM_start_clsd_D: {NOTAM_start_clsd_D}")
                                print(f"NOTAM_end_clsd_D: {NOTAM_end_clsd_D}")
                            else:
                                print("D) section exists but is empty.")


                        # Extract purpose of the NOTAM (E) section)
                        if identifier == 'E' and NOTAM_purpose is None:
                            NOTAM_purpose = content.strip()
                            #print(f"Content: {content}")
                            print(f"NOTAM_purpose: {NOTAM_purpose}")

                        #Do something if NOTAM_purpose has a value and none of the variations are found in it
                        if NOTAM_purpose and not any(variation in NOTAM_purpose for variation in NOTAM.PURPOSE_VARIATIONS):
                            print("Not schedule NOTAM.")
                            NOTAM_end_date = None
                            NOTAM_purpose = None
                            NOTAM_start_date = None
                            NOTAM_start_hour = None
                            NOTAM_end_hour = None
                            break
                        elif NOTAM_start_date and NOTAM_end_date and NOTAM_purpose:
                        # Directly compare the start and end date with current_date (both are in YYMMDD format)
                            if NOTAM_start_date <= formatted_date <= NOTAM_end_date:
                                found_NOTAM = True
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
 
 
