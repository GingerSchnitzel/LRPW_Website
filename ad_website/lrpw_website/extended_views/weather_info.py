# utils.py
import requests
from datetime import datetime, timedelta

# Function to get the most recent non-empty value from the list
def get_most_recent_data(data_list):
    # Reverse the list and find the first non-empty value
    for value in reversed(data_list):
        if value:  # Check if the value is not an empty string
            return float(value)
    return 0  # Return None if no valid data is found

def fetch_weather_data():
    """Fetches weather data from API and saves it to the database."""
    url = "https://www.ecowitt.net/index/get_data"
    
    current_time = datetime.now()
    one_hour_ago = current_time - timedelta(hours=1)

    sdate = one_hour_ago.strftime("%Y-%m-%d %H:%M")
    edate = current_time.strftime("%Y-%m-%d %H:%M")

    payload = {
        "device_id": "a3pwZkZoQWdGS1VqNHo3aG9qRVlRQT09",
        "is_list": "0",
        "mode": "0",
        "sdate": sdate,
        "edate": edate,
        "page": "1",
        "authorize": "R11QNW",
        "sortList": "0|1|2|3|4|5|999",
        "hideList": ""
    }

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        data = response.json()
        weather_data = {
    'outdoor_temp': get_most_recent_data(data['list']['tempf']['list']['tempf'][1:]),
    'outdoor_feels_like': get_most_recent_data(data['list']['tempf']['list']['sendible_temp'][1:]),
    'outdoor_dew_point': get_most_recent_data(data['list']['tempf']['list']['drew_temp'][1:]),
    'outdoor_humidity': int(get_most_recent_data(data['list']['humidity']['list']['humidity'][1:])),
    'indoor_temp': get_most_recent_data(data['list']['tempinf']['list']['tempinf'][1:]),
    'indoor_humidity': int(get_most_recent_data(data['list']['humidityin']['list']['humidityin'][1:])),
    'solar_radiation': get_most_recent_data(data['list']['so_uv']['list']['solarradiation'][1:]),
    'uv_index': int(get_most_recent_data(data['list']['so_uv']['list']['uv'][1:])),
    'rain_rate': get_most_recent_data(data['list']['rain']['list']['rainratein'][1:]),
    'daily_rain': get_most_recent_data(data['list']['rain']['list']['dailyrainin'][1:]),
    'weekly_rain': get_most_recent_data(data['list']['rain_statistcs']['list']['weeklyrainin'][1:]),
    'monthly_rain': get_most_recent_data(data['list']['rain_statistcs']['list']['monthlyrainin'][1:]),
    'yearly_rain': get_most_recent_data(data['list']['rain_statistcs']['list']['yearlyrainin'][1:]),
    'wind_speed': get_most_recent_data(data['list']['wind_speed']['list']['windspeedmph'][1:]),
    'wind_gust': get_most_recent_data(data['list']['wind_speed']['list']['windgustmph'][1:]),
    'wind_direction': int(get_most_recent_data(data['list']['winddir']['list']['winddir'][1:])),
    'relative_pressure': get_most_recent_data(data['list']['pressure']['list']['baromrelin'][1:]),
    'absolute_pressure': get_most_recent_data(data['list']['pressure']['list']['baromabsin'][1:]),
    'last_update_time': data['times'][-1]  # Most recent time
}

        print(weather_data)
        return weather_data
    else:
        print("Error fetching data:", response.status_code)
        return None