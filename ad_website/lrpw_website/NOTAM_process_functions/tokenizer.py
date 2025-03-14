from datetime import date, datetime, timedelta
from enum import Enum
from typing import List, Tuple, Optional
import re
from dateutil.parser import parse


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

def parse_year(yy_mm_dd: str) -> datetime:
    try:
        # Attempt to parse the date string
        return datetime.strptime(yy_mm_dd, "%y%m%d")
    except ValueError:
        # Raise a ValueError with a custom error message if parsing fails
        raise ValueError(f"Invalid date format or invalid date: {yy_mm_dd}")

def make_day_range(start: Day, end: Day, start_date: str, end_date: str) -> List[Day]:
    start_dt = parse_year(start_date)
    end_dt = parse_year(end_date)

    if start == Day.INVALID or end == Day.INVALID:
        return []
    
    if start_dt.weekday() + 1 == start.value and end_dt.weekday() + 1 == end.value:
         # Special case: spanning multiple weeks
        result = []
        current_date = start_dt
        while current_date <= end_dt:
            result.append(Day(current_date.weekday() + 1))
            current_date += timedelta(days=1)
        return result
    
    if start == end:
        # When start and end are the same, return all days in order, wrapping around
        return [Day(day) for day in range(start.value, len(Day))] + [Day(day) for day in range(1, start.value + 1)]
    elif start.value < end.value:
        # Sequential range (e.g., MON to THU)
        return [Day(day) for day in range(start.value, end.value + 1)]
    else:
        # Wrapping range (e.g., FRI to MON)
        return [Day(day) for day in range(start.value, len(Day))] + [Day(day) for day in range(1, end.value + 1)]


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

def parse_date(token: str) -> Optional[str]:
    try:
        current_date = datetime.now()  # Get the current date and time
        current_year = current_date.year  # Get the current year

        # Handle cases with two parts: "DD MMM"
        if len(token.split()) == 2:
            # Parse the date with the current year and the previous year
            date_with_current_year = parse(f"{token} {current_year}")
            date_with_previous_year = parse(f"{token} {current_year - 1}")
            date_with_next_year = parse(f"{token} {current_year + 1}")

            # Determine which date is closer to today
            parsed_date = min(
                [date_with_previous_year, date_with_current_year, date_with_next_year],
                key=lambda d: abs((d - current_date).total_seconds())
            )

        # Handle cases with three parts: "DD MMM YYYY"
        elif len(token.split()) == 3:
            parsed_date = parse(token)

        # Invalid format
        else:
            return None

        # Format the date as "FRI, 10 JAN 2025"
        formatted_date = parsed_date.strftime("%a, %d %b %Y").upper()
        return formatted_date

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

def generate_date_range(start_date_str: str, end_date_str: str) -> List[str]:
    """
    Generates all dates between start_date and end_date inclusive, given start_date and end_date
    in the format 'DAY, DD MON YYYY' (e.g., 'FRI, 10 JAN 2025').

    Args:
        start_date_str (str): The start date in the format 'DAY, DD MON YYYY'.
        end_date_str (str): The end date in the format 'DAY, DD MON YYYY'.

    Returns:
        List[datetime]: A list of datetime objects representing all dates in the range.
    """
    try:
        # Parse the input strings into datetime objects
        start_date = datetime.strptime(start_date_str, "%a, %d %b %Y")
        end_date = datetime.strptime(end_date_str, "%a, %d %b %Y")
        
        # Check if start_date is before end_date
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date.")
        
        # Generate the list of dates
        delta = end_date - start_date
        return [(start_date + timedelta(days=i)).strftime("%a, %d %b %Y").upper() for i in range(delta.days + 1)]
    except ValueError as e:
        print(f"Error parsing dates: {e}")
        return []
    
def peek(tokens, index, offset=1):
    """Safely get the next token(s) in the list."""
    if index + offset < len(tokens):
        return tokens[index + offset]
    return None

# Parsing Functions
def get_time_groups(tokens: List[str], start_dt: str, end_dt: str) -> List[Tuple[List[datetime], List[str]]]:
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

    for i, token in enumerate(tokens):
        token_type = get_type(token)

        if state == State.START:
            if token_type == TokenType.DAY:
                next_token = peek(tokens, i)
                if not is_date(next_token):
                    current_dates.append(get_day(token))
                state = State.GOT_DAY
            elif token_type == TokenType.DATE:
                current_dates.append(parse_date(token))
                state = State.GOT_DATE
            else:
                raise ValueError(f"Unexpected token at start: {token}")

        elif state == State.GOT_DATE:
            if token_type == TokenType.DAY:
                next_token = peek(tokens, i)
                if not is_date(next_token):
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
                next_token = peek(tokens, i)
                if not is_date(next_token):
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
                next_token = peek(tokens, i)
                if not is_date(next_token):
                    # Handle dash between days
                    start_day = current_dates[-1]
                    end_day = get_day(token)
                    day_range = make_day_range(start_day, end_day, start_dt, end_dt)
                    current_dates.extend(day_range[1:])  # Avoid duplicating the first day
                    state = State.GOT_DAY
            elif token_type == TokenType.DATE:
                # Handle dash between dates
                start_date = current_dates[-1]
                end_date = parse_date(token)
                date_range = generate_date_range(start_date, end_date)
                current_dates.extend(date_range[1:])
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
                current_dates = []
                current_time_ranges = []
                next_token = peek(tokens, i)
                if not is_date(next_token):
                    current_dates = [get_day(token)]
                state = State.GOT_DAY
            else:
                raise ValueError(f"Unexpected token after time range: {token}")

    if current_dates and current_time_ranges:
        time_groups.append((current_dates, current_time_ranges))

    return time_groups