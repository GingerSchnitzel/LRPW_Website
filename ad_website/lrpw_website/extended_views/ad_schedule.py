import requests
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import re
from ..NOTAM_process_functions.parse_NOTAM_content import parse_NOTAM_contents
from ..NOTAM_process_functions.eet_time_converter import convert_schedule_to_eet
from ..models import NOTAM_model
import traceback

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
def scrape_notams(NOTAMS_URL=NOTAM.URL):
    try:
        session = requests.Session()
        session.mount("https://", TLSAdapter())

        certificate_path = './certificates/cert.pem'
        response = session.get(NOTAMS_URL, verify=certificate_path)

        if response.status_code != 200:
            return {'message': f"Failed to fetch NOTAMs. Status code: {response.status_code}"}

        soup = BeautifulSoup(response.content, 'html.parser')
        #current_date = date.today()
        #current_YYMMDD_date = current_date.strftime("%y%m%d")  

        for notam_entry in soup.find_all("div", style="font-family:monospace; font-size:large;"):
            notam_decoded = notam_entry.decode_contents().strip()
            notam_decoded = re.sub(r'<\?xml .*?\?>', '', notam_decoded).strip()
            notam_soup = BeautifulSoup(notam_decoded, 'html.parser')
            notam_text = notam_soup.get_text(separator=' ', strip=True).strip("()").strip()

            if notam_text.startswith(NOTAM.SERIES_A):  # Only Series A NOTAMs
                match = re.match(r'^A\d{4}/\d{2}', notam_text)
                if not match:
                    continue

                NOTAM_series = str(match.group(0))
                NOTAM_number = int(NOTAM_series[1:5])
                NOTAM_year = int(NOTAM_series[-2:]) + 2000  

                NOTAM_ad_open = False
                NOTAM_start_date = None
                NOTAM_end_date = None
                NOTAM_start_hour = None
                NOTAM_end_hour = None
                NOTAM_schedule = []

                sections = re.findall(r'([A-Z])\)\s*(.*?)(?=(?: [A-Z]\)|$))', notam_text)

                for identifier, content in sections:
                    try:
                        if identifier == 'B':
                            NOTAM_start_date = content.strip()[:6]
                            NOTAM_start_hour = content.strip()[6:]

                        if identifier == 'C':
                            NOTAM_end_date = content.strip()[:6]
                            NOTAM_end_hour = content.strip()[6:]

                        if identifier == 'D' and not NOTAM_schedule:
                            NOTAM_schedule = parse_NOTAM_contents(NOTAM_start_date, NOTAM_end_date, content)

                        if identifier == 'E' and not NOTAM_schedule and NOTAM_ad_open == False:
                            NOTAM_section_E = content.strip()
                            
                            if NOTAM.AD_CLOSED in NOTAM_section_E:
                                NOTAM_ad_open = False
                            elif NOTAM.AD_OPEN in NOTAM_section_E:
                                NOTAM_ad_open = True
                            else:
                                continue
                            
                            if NOTAM_section_E != NOTAM.AD_CLOSED:
                                extracted_NOTAM_schedule = parse_NOTAM_contents(NOTAM_start_date, NOTAM_end_date, NOTAM_section_E)
                                NOTAM_schedule = convert_schedule_to_eet(extracted_NOTAM_schedule)

                            if not NOTAM_schedule and NOTAM_ad_open == False and NOTAM.AD_CLOSED == NOTAM_section_E:
                                start_date_obj = datetime.strptime(NOTAM_start_date, "%y%m%d")
                                formatted_start_date = start_date_obj.strftime("%a, %d %b %Y").upper()

                                end_date_obj = datetime.strptime(NOTAM_end_date, "%y%m%d")
                                formatted_end_date = end_date_obj.strftime("%a, %d %b %Y").upper()

                                if NOTAM_start_date != NOTAM_end_date:
                                    section_E_closed = f"{formatted_start_date} - {formatted_end_date}: CLSD"
                                else:
                                    section_E_closed = f"{formatted_start_date}: CLSD"
                                
                                NOTAM_schedule =  parse_NOTAM_contents(NOTAM_start_date, NOTAM_end_date, section_E_closed)
                               
                    except Exception as e:
                        print(f"Error processing section {identifier}: {e}")

                if NOTAM_start_date and NOTAM_end_date and NOTAM_schedule:
                    #if NOTAM_start_date <= current_YYMMDD_date <= NOTAM_end_date:
                    notam_data = {
                        'series': NOTAM_series,
                        'number': NOTAM_number,
                        'year': NOTAM_year,
                        'ad_open': NOTAM_ad_open,
                        'start_date': NOTAM_start_date,
                        'start_hour': NOTAM_start_hour,
                        'end_date': NOTAM_end_date,
                        'end_hour': NOTAM_end_hour,
                        'schedule': NOTAM_schedule,
                        'notam_RAW_text': notam_text,
                    }

                    # Check if NOTAM already exists before saving
                    existing_notam = NOTAM_model.objects.filter(series=NOTAM_series, number=NOTAM_number, year=NOTAM_year).first()
                    if existing_notam:
                        print(f"NOTAM {NOTAM_series} already exists in the database. Skipping...")
                    else:
                        new_notam = NOTAM_model(**notam_data)
                        new_notam.save()
                        print(f"Saved new NOTAM: {NOTAM_series}")

        return {'message': 'NOTAM data processing completed.'}

    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
 
