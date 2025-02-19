from datetime import datetime, timezone, timedelta
from django.utils.timezone import make_aware

def get_default_schedule(notams):
    """
    Determines the aerodrome's schedule based on NOTAMs or the default schedule.
    :param notams: A queryset of NOTAM_model instances valid for today.
    :return: String with the schedule in the format "Mon, DD.MM.YYYY HH:MM - HH:MM UTC" or "CLOSED".
    """

    now_utc = datetime.now(timezone.utc)
    weekday = now_utc.weekday()  # Monday = 0, Sunday = 6

    # If there are valid NOTAMs for today, check if any specifies an opening schedule
    if notams.exists():
        for notam in notams:
            start_datetime = datetime.strptime(notam.start_date + (notam.start_hour), '%y%m%d%H%M')
            end_datetime = datetime.strptime(notam.end_date + (notam.end_hour), '%y%m%d%H%M')
            start_datetime = make_aware(start_datetime, timezone.utc)
            end_datetime = make_aware(end_datetime, timezone.utc)

            if start_datetime <= now_utc <= end_datetime:
                if notam.ad_open:
                    return True  # If NOTAM says open, return True
                else:
                    return False  # If NOTAM says closed, return False

    # If no NOTAMs exist, use the default schedule
    if weekday >= 5:  # Saturday (5) or Sunday (6) => Aerodrome is closed
        return f"{now_utc.strftime('%a, %d.%m.%Y')} CLSD"

    # Determine if we are in winter (EET, UTC+2) or summer (EEST, UTC+3)
    last_sunday_march = max(day for day in range(25, 32) if datetime(now_utc.year, 3, day).weekday() == 6)  # Last Sunday of March
    last_sunday_october = max(day for day in range(25, 32) if datetime(now_utc.year, 10, day).weekday() == 6)  # Last Sunday of October

    if now_utc.month > 3 and now_utc.month < 10:  # Between April and September, always summer
        summer_time = True
    elif now_utc.month == 3 and now_utc.day >= last_sunday_march:
        summer_time = True
    elif now_utc.month == 10 and now_utc.day < last_sunday_october:
        summer_time = True
    else:
        summer_time = False

    # Set the default operating hours based on season
    if summer_time:
        open_hour_utc, close_hour_utc = 4, 12  # Summer (UTC+3 -> UTC)
    else:
        open_hour_utc, close_hour_utc = 5, 13  # Winter (UTC+2 -> UTC)

    # Format and return the schedule
    return [f"{now_utc.strftime('%a, %d.%m.%Y')} {open_hour_utc:02}:00 - {close_hour_utc:02}:00"]

