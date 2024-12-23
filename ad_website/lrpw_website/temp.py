import requests
from bs4 import BeautifulSoup
from datetime import date, datetime
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

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
                          'TEMPORARY CHANGE OF AD ADMINISTRATION OPS HOURS .']
    SERIES_A = 'A'
    XML = 'xml version='
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
        
        # Iterate over all the NOTAMs on the page (assuming each <a> tag represents a NOTAM)
        for notam_entry in soup.find_all('div'):
              
            notam_text = notam_entry.text.strip()
            if NOTAM.XML in notam_text:
                print(f"Processing NOTAM: {notam_text}")

                if notam_text.startswith(NOTAM.SERIES_A):  # Check if the NOTAM starts with 'A'
                    NOTAM_series = NOTAM.SERIES_A
                    NOTAM_purpose = None
                    NOTAM_start_date = None
                    NOTAM_end_date = None

                    # Extract the details of the NOTAM
                    for line in soup.text.splitlines():
                        # Extract purpose of the NOTAM (E) section)
                        if line.strip().startswith('E)') and NOTAM_purpose is None:
                            NOTAM_purpose = line.strip()[3:]

                        # Check if the NOTAM's purpose matches any variation
                        if NOTAM_purpose in NOTAM.PURPOSE_VARIATIONS:
                            # Extract the start date (B) section)
                            if line.strip().startswith('B)') and NOTAM_start_date is None:
                                NOTAM_start_date = line.strip()[3:9]

                            # Extract the end date (C) section)
                            if line.strip().startswith('C)') and NOTAM_end_date is None:
                                NOTAM_end_date = line.strip()[3:9]

                    # After extracting the details, we compare the dates
                    if NOTAM_start_date and NOTAM_end_date:
                        # Directly compare the start and end date with current_date (both are in YYMMDD format)
                        if NOTAM_start_date <= formatted_date <= NOTAM_end_date:
                            found_NOTAM = True
                            print("Valid NOTAM found:", notam_text)
                            return {
                                'notam_text': notam_text,
                                'purpose': NOTAM_purpose,
                                'start_date': NOTAM_start_date,
                                'end_date': NOTAM_end_date,
                            }

        print("No valid NOTAMs found.")
        return {'message': 'No valid NOTAMs found for today.'}

    except Exception as e:
        print(f"An error occurred: {e}")
 
import httpx

def scrape_notams_httpx(NOTAMS_URL=NOTAM.URL):
    try:
        print(f"Sending request to: {NOTAMS_URL}")

        # Configure httpx with a lower security level
        transport = httpx.HTTPTransport(verify=False)
        with httpx.Client(transport=transport) as client:
            response = client.get(NOTAMS_URL, timeout=10.0)
            print(f"Response status code: {response.status_code}")

            if response.status_code != 200:
                return {'message': f"Failed to fetch NOTAMs. Status code: {response.status_code}"}

            soup = BeautifulSoup(response.content, 'html.parser')
            # Process response content as needed
            print("Response content parsed successfully.")
            return {'content': soup.prettify()}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {'message': str(e)}