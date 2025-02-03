from typing import List, Tuple, Optional
from tokenizer import get_time_groups, Day

def process_tokens(tokens: List[str], start_date: str, end_date: str):
    """
    Processes a list of tokens representing NOTAM information and organizes them into 
    a structured list of tuples containing day/date and corresponding time ranges.

    Args:
        tokens (List[str]): A list of tokens representing NOTAM days, dates, and time ranges.

    Returns:
        List[Tuple[str, str]]: A list of tuples where each tuple contains:
                                - A formatted day (e.g., "MON") or full date (e.g., "FRI, 10 JAN 2025").
                                - A string representing the time range.
    """
    notam_data = []  # This will store the processed day/date and time range information.

    try:
        # Extract day/date and time range groups from tokens using a helper function.
        time_groups = get_time_groups(tokens, start_date, end_date)

        # Iterate through the extracted groups of days/dates and time ranges.
        for days, time_ranges in time_groups:
            for date in days:
                # Handle case where the token is a day name (e.g., "MON", "FRI").
                if isinstance(date, Day):
                    # Convert the day enum to its string representation (e.g., "MON").
                    date_str = date.name  

                    # Add the day entry only if a full date entry for the same day 
                    # doesn't already exist with the same time range.
                    if not notam_data or notam_data[-1][0] != date_str or notam_data[-1][1] != time_ranges:
                        notam_data.append((date_str, time_ranges))
                        continue


                # Handle case where the token is a date range (e.g., "MON, 01 JAN").
                elif ',' in date:
                    date_str = date

                     # Check if the last entry in the list has the same day and time range
                    if notam_data and notam_data[-1][0] == date_str[:3] and notam_data[-1][1] == time_ranges:
                        notam_data.pop()  # Remove the last entry

                # Uncomment this section if handling full datetime objects is required.
                '''
                elif isinstance(date, datetime):
                    # Format the datetime object to a string (e.g., "FRI, 10 JAN 2025").
                    day_date = date.strftime('%a, %d %b %Y').upper()

                    # Remove any existing entry for the corresponding day-only entry 
                    # with the same time range.
                    notam_data = [
                        (d, t) for d, t in notam_data
                        if not (d == date_str and t == time_ranges)
                    ]
                '''

                # Add the full date or date range to the list.
                notam_data.append((date_str, time_ranges))
        
        # Return the processed list of NOTAM data.
        return notam_data

    # Handle specific error cases during processing.
    except ValueError as e:
        print("Error:", e)
        return []
    except Exception as e:
        # Catch any unexpected errors and print the error message.
        print(f"An unexpected error occurred: {e}")
        return []

