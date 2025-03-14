import os
import django
import re
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock
import pdb

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ad_website.settings')
django.setup()

# Now import your modules
from lrpw_website.extended_views.ad_schedule import scrape_notams
from lrpw_website.NOTAM_process_functions.parse_NOTAM_content import parse_NOTAM_contents
from lrpw_website.NOTAM_process_functions.eet_time_converter import convert_schedule_to_eet
from lrpw_website.models import NOTAM_model

# Mock the HTML response
mock_html = """
<div style="font-family:monospace; font-size:large;">
    A0100/2025	LRCN	
(A0100/25 NOTAMR A0083/25
Q) LRBB/QFAAH/IV/BO /A /000/999/4422N02556E005
A) LRCN B) 2501101223 C) 2501201300
E) TEMPORARY CHANGE OF AD ADMINISTRATION OPS HOURS AS FLW:
FRI, 10 JAN 2025: 0800-1500
SAT, 11 JAN 2025: CLSD
SUN, 12 JAN 2025: CLSD
MON, 13 JAN 2025: 0800-1300
TUE, 14 JAN 2025: 0800-1300
WED, 15 JAN 2025: 0800-1300
THU, 16 JAN 2025: 0800-1300
FRI, 17 JAN 2025: 0800-1300
SAT, 18 JAN 2025: CLSD
SUN, 19 JAN 2025: CLSD
MON, 20 JAN 2025: 0800-1300)
"""

mock_html1 = """
<div style="font-family:monospace; font-size:large;">
A4368/23 NOTAMN
Q) LRBB/QFAAH/IV/BO /A /000/999/4455N02558E005
A) LRPW B) 2309161147 C) 2309161300
E) TEMPORARY CHANGE OF AD ADMINISTRATION OPS HOURS
AD CLSD:
SAT, 16 SEP 2023: 1130-1300
"""

mock_html2 = """
<div style="font-family:monospace; font-size:large;">
(A0885/25 NOTAMR A0880/25
Q) LRBB/QMRLT/IV/NBO/A /000/999/4430N02606E005
A) LRBS B) 2502211326 C) 2502221500
D) FRI 1340-1500, SAT 0600-0700 0800-1200 1330-1500
E) LANDING ON RWY 07 IS NOT PERMITTED)
"""

mock_html3 = """
<div style="font-family:monospace; font-size:large;">
(A2225/23 NOTAMR A2197/23
Q) LRBB/QFALC/IV/NBO/A /000/999/4455N02558E005
A) LRPW B) 2306020839 C) 2306051200
D) FRI 0400-1029 1101-1200, MON 0400-1200
E) AD CLSD FOR AIR TRAFFIC))
"""

mock_html4 = """
<div style="font-family:monospace; font-size:large;">
(A4650/24 NOTAMN
Q) LRBB/QFAAH/IV/BO /A /000/999/4455N02558E005
A) LRPW B) 2408080330 C) 2408170900
E) TEMPORARY CHANGE OF AD ADMINISTRATION OPS HOURS.
AD OPEN AS FLW:
DAILY 0330-0900)
"""



def debug_notam_parsing():
    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(mock_html3, 'html.parser')
    
    print("1. Finding NOTAM entries...")
    notam_entries = soup.find_all("div", style="font-family:monospace; font-size:large;")
    print(f"   Found {len(notam_entries)} NOTAM entries")
    
    # Process each NOTAM entry
    for notam_entry in notam_entries:
        notam_decoded = notam_entry.decode_contents().strip()
        notam_decoded = re.sub(r'<\?xml .*?\?>', '', notam_decoded).strip()
        notam_soup = BeautifulSoup(notam_decoded, 'html.parser')
        notam_text = notam_soup.get_text(separator=' ', strip=True).strip("()").strip()
        
        print(f"2. Raw NOTAM text: {notam_text}")
        
        # Check if it's a Series A NOTAM
        if notam_text.startswith("A"):
            print("3. This is a Series A NOTAM")
            match = re.match(r'^A\d{4}/\d{2}', notam_text)
            if match:
                NOTAM_series = str(match.group(0))
                NOTAM_number = int(NOTAM_series[1:5])
                NOTAM_year = int(NOTAM_series[-2:]) + 2000
                
                print(f"4. NOTAM details: Series={NOTAM_series}, Number={NOTAM_number}, Year={NOTAM_year}")
                
                # Initialize variables
                NOTAM_ad_open = False
                mixed_open_close = False
                section_D_parsed = False
                NOTAM_start_date = None
                NOTAM_end_date = None
                NOTAM_start_hour = None
                NOTAM_end_hour = None
                NOTAM_schedule = None
                
                # Parse sections
                print("5. Parsing NOTAM sections...")
                sections = re.findall(r'([A-Z])\) ([\s\S]+?)(?=[A-Z]\) |$)', notam_text)
                
                for identifier, content in sections:
                    print(f"   Section {identifier}: {content[:50]}...")
                    
                    try:
                        if identifier == 'B':
                            NOTAM_start_date = content.strip()[:6]
                            NOTAM_start_hour = content.strip()[6:]
                            print(f"   Extracted start date: {NOTAM_start_date}, hour: {NOTAM_start_hour}")
                            
                        if identifier == 'C':
                            NOTAM_end_date = content.strip()[:6]
                            NOTAM_end_hour = content.strip()[6:]
                            print(f"   Extracted end date: {NOTAM_end_date}, hour: {NOTAM_end_hour}")
                            
                        if identifier == 'D' and not NOTAM_schedule:
                            if content.strip():
                                print("   Attempting to parse schedule from section D")
                                extracted_schedule = parse_NOTAM_contents(NOTAM_start_date, NOTAM_end_date, content)
                                print(f"   Raw extracted schedule: {extracted_schedule}")
                                NOTAM_schedule = convert_schedule_to_eet(extracted_schedule)
                                print(f"   Converted schedule: {NOTAM_schedule}")
                                # Add "OPEN" as the first element in the schedule list
                                if NOTAM_schedule:
                                    NOTAM_schedule = [["CLOSED"] + schedule_item for schedule_item in NOTAM_schedule]  # Prepend "CLOSED" to each inner list
                                print(f"   Section D schedule: {NOTAM_schedule}")
                                
                                section_D_parsed = True
                                print(f"section_D_parsed: {section_D_parsed}")
                            
                        if identifier == 'E':
                            NOTAM_section_E = content.strip()
                            if section_D_parsed == True and "AD CLSD" not in NOTAM_section_E and "TEMPORARY CHANGE OF AD ADMINISTRATION OPS HOURS" not in NOTAM_section_E:
                                    print("Section D extracted, but not schedule NOTAM. Skipping.")
                                    print(f"Section D contents: {NOTAM_schedule}")
                                    print(f"But section E contents: {NOTAM_section_E}")
                                    NOTAM_schedule = []
                                    continue
                            
                            if not NOTAM_schedule:
                                
                                print(f"   Section E content: {NOTAM_section_E[:100]}...")
                                
                                # Special handling for E section
                                print(f"   Contains 'AD CLSD': {'AD CLSD' in NOTAM_section_E}")
                                print(f"   Contains 'TEMPORARY CHANGE': {'TEMPORARY CHANGE OF AD ADMINISTRATION OPS HOURS' in NOTAM_section_E}")
                                
                                if "AD CLSD" in NOTAM_section_E:
                                    NOTAM_ad_open = False
                                    print("   Setting AD status: CLOSED")
                                elif "TEMPORARY CHANGE OF AD ADMINISTRATION OPS HOURS" in NOTAM_section_E:
                                    NOTAM_ad_open = True
                                    print("   Setting AD status: OPEN (temporary change)")

                                if "TEMPORARY CHANGE OF AD ADMINISTRATION OPS HOURS" in NOTAM_section_E and "AD CLSD" in NOTAM_section_E:
                                    mixed_open_close = True
                                    print("    Ad status: mixed")

                                if NOTAM_section_E != "AD CLSD":
                                    print("   Attempting to parse schedule from section E")
                                    extracted_NOTAM_schedule = parse_NOTAM_contents(NOTAM_start_date, NOTAM_end_date, NOTAM_section_E)
                                    print(f"   Raw extracted schedule: {extracted_NOTAM_schedule}")
                                    
                                    if extracted_NOTAM_schedule:
                                        print("   Converting schedule to EET")
                                        NOTAM_schedule = convert_schedule_to_eet(extracted_NOTAM_schedule)
                                        print(f"   Converted schedule: {NOTAM_schedule}")
                                
                                # Special case handling
                                if not NOTAM_schedule and NOTAM_ad_open == False and "AD CLSD" == NOTAM_section_E :
                                    print("   Creating fallback schedule for AD CLSD")
                                    
                                    from datetime import datetime
                                    start_date_obj = datetime.strptime(NOTAM_start_date, "%y%m%d")
                                    formatted_start_date = start_date_obj.strftime("%a, %d %b %Y").upper()
                                    
                                    end_date_obj = datetime.strptime(NOTAM_end_date, "%y%m%d")
                                    formatted_end_date = end_date_obj.strftime("%a, %d %b %Y").upper()
                                    
                                    if NOTAM_start_date != NOTAM_end_date:
                                        section_E_closed = f"{formatted_start_date} - {formatted_end_date}: CLSD"
                                    else:
                                        section_E_closed = f"{formatted_start_date}: CLSD"
                                    
                                    print(f"   Fallback section E: {section_E_closed}")
                                    NOTAM_schedule = convert_schedule_to_eet(parse_NOTAM_contents(NOTAM_start_date, NOTAM_end_date, section_E_closed))
                                
                                print(f"Before update: {NOTAM_schedule}")
                                if NOTAM_schedule:
                                    for i, schedule_item in enumerate(NOTAM_schedule):
                                        # Ensure the schedule_item is a list with at least 2 elements before proceeding
                                        if isinstance(schedule_item, list) and len(schedule_item) >= 2:
                                            # Check if "CLSD" is in the second element (schedule_item[1])
                                            if "CLSD" in schedule_item[1] or mixed_open_close == True:
                                                NOTAM_schedule[i] = ["CLOSED"] + schedule_item  # Prepend "CLOSED" to the list
                                            else:
                                                NOTAM_schedule[i] = ["OPEN"] + schedule_item  # Prepend "OPEN" to the list
                                        else:
                                            print(f"   Skipping invalid schedule item: {schedule_item}")
                                print(f"After update: {NOTAM_schedule}")
                                print(f"   Fallback schedule: {NOTAM_schedule}")
                    
                    except Exception as e:
                        print(f"   ERROR processing section {identifier}: {e}")
                
                # Check if we have enough data to create a NOTAM
                print("\n6. Final NOTAM data:")
                print(f"   Series: {NOTAM_series}")
                print(f"   Number: {NOTAM_number}")
                print(f"   Year: {NOTAM_year}")
                print(f"   AD Open: {NOTAM_ad_open}")
                print(f"   Start Date: {NOTAM_start_date}")
                print(f"   End Date: {NOTAM_end_date}")
                print(f"   Schedule: {NOTAM_schedule}")
                
                if NOTAM_start_date and NOTAM_end_date and NOTAM_schedule:
                    print("   ✅ NOTAM has all required fields")
                else:
                    print("   ❌ NOTAM is missing required fields")
                    if not NOTAM_start_date:
                        print("      Missing start date")
                    if not NOTAM_end_date:
                        print("      Missing end date")
                    if not NOTAM_schedule:
                        print("      Missing schedule")
            else:
                print("   Not a valid Series A NOTAM format")

# Execute the debugging function
if __name__ == "__main__":
    print("=== Starting NOTAM Parsing Debug ===")
    
    # If you want interactive debugging, uncomment this:
    # pdb.set_trace()
    
    debug_notam_parsing()
    
    print("\n=== Simulating actual scrape_notams() function call ===")
    # Mock the requests.Session.get to return our mock HTML
    with patch('requests.Session.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = mock_html3.encode("utf-8")
        mock_get.return_value = mock_response
        
        # Skip certificate verification for debugging
        with patch('lrpw_website.extended_views.ad_schedule.TLSAdapter') as mock_adapter:
            # Also patch NOTAM_model.objects.filter to avoid DB checks
            with patch('lrpw_website.models.NOTAM_model.objects.filter') as mock_filter:
                mock_filter.return_value.first.return_value = None
                
                try:
                    print("Calling scrape_notams()...")
                    result = scrape_notams()
                    print(f"Result: {result}")
                except Exception as e:
                    print(f"Error in scrape_notams(): {e}")
                    import traceback
                    traceback.print_exc()