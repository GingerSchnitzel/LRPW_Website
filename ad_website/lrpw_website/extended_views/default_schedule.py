from datetime import datetime, timezone, timedelta
from django.utils.timezone import make_aware

def get_default_schedule(notams, date):
    """
    Determines the aerodrome's schedule based on NOTAMs or the default schedule.
    :param notams: A queryset of NOTAM_model instances valid for the given date.
    :param date: A datetime.date object representing the day for which to get the schedule.
    :return: List containing a single formatted schedule string.
    """
    target_datetime = datetime(date.year, date.month, date.day, tzinfo=timezone.utc)
    weekday = target_datetime.weekday()  # Monday = 0, Sunday = 6

    # Check NOTAMs for the given date
    if notams.exists():
        for notam in notams:
            start_datetime = datetime.strptime(notam.start_date + notam.start_hour, '%y%m%d%H%M')
            end_datetime = datetime.strptime(notam.end_date + notam.end_hour, '%y%m%d%H%M')
            start_datetime = make_aware(start_datetime, timezone.utc)
            end_datetime = make_aware(end_datetime, timezone.utc)

            if start_datetime.date() <= date <= end_datetime.date():
                if notam.ad_open:
                    return [f"{target_datetime.strftime('%a, %d.%m.%Y')} OPEN"]
                else:
                    return [f"{target_datetime.strftime('%a, %d.%m.%Y')}, CLSD"]

    # If no NOTAMs exist, use the default schedule
    if weekday >= 5:  # Saturday (5) or Sunday (6) => Aerodrome is closed
        return [f"{target_datetime.strftime('%a, %d.%m.%Y')}, CLSD"]

    # Determine if the given date is in summer (EEST, UTC+3) or winter (EET, UTC+2)
    last_sunday_march = max(day for day in range(25, 32) if datetime(date.year, 3, day).weekday() == 6)  # Last Sunday of March
    last_sunday_october = max(day for day in range(25, 32) if datetime(date.year, 10, day).weekday() == 6)  # Last Sunday of October

    if (date.month > 3 and date.month < 10) or (date.month == 3 and date.day >= last_sunday_march) or (date.month == 10 and date.day < last_sunday_october):
        summer_time = True
    else:
        summer_time = False

    # Set the default operating hours based on season
    if summer_time:
        open_hour_utc, close_hour_utc = 4, 12  # Summer (UTC+3 -> UTC)
    else:
        open_hour_utc, close_hour_utc = 5, 13  # Winter (UTC+2 -> UTC)

    # Return schedule in a list format
    return [f"{target_datetime.strftime('%a, %d.%m.%Y')} {open_hour_utc:02}:00 - {close_hour_utc:02}:00"]
