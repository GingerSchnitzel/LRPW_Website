import unittest
from datetime import datetime
from typing import List
from token_processor_dates import (  # Replace 'your_module' with the actual module name
    get_next_day_name,
    parse_date_from_yyyymmdd,
    get_weekday_date,
    format_date,
    process_weekdays_with_dates,
    Day
)

class TestDateProcessingFunctions(unittest.TestCase):

    def test_get_next_day_name(self):
        """Test getting the next day name."""
        self.assertEqual(get_next_day_name("MON"), "TUE")
        self.assertEqual(get_next_day_name("SUN"), "MON")
        self.assertIsNone(get_next_day_name("INVALID"))

    def test_parse_date_from_yyyymmdd(self):
        """Test parsing a date from YYMMDD format."""
        self.assertEqual(parse_date_from_yyyymmdd("250122"), datetime(2025, 1, 22))
        self.assertRaises(ValueError, parse_date_from_yyyymmdd, "invalid")

    def test_get_weekday_date(self):
        """Test getting the next date for a given weekday."""
        start_date = datetime(2025, 1, 22)  # Wednesday
        self.assertEqual(get_weekday_date(start_date, Day.MON), datetime(2025, 1, 27))
        self.assertEqual(get_weekday_date(start_date, Day.WED), datetime(2025, 1, 22))
        self.assertEqual(get_weekday_date(start_date, Day.SUN), datetime(2025, 1, 26))

    def test_format_date(self):
        """Test formatting a datetime object to a specific string format."""
        date = datetime(2025, 1, 22)
        self.assertEqual(format_date(date), "WED, 22 JAN 2025")

    def test_process_weekdays_with_dates(self):
        """Test processing weekdays with associated dates."""
        start_date = "250122"  # 22 January 2025
        end_date = "250128"  # 28 January 2025

        notam_data = [
            ["MON", ["0800-1500"]],
            ["TUE", ["0900-1600"]],
            ["WED, 22 JAN 2025", ["1000-1700"]],
            ["FRI", ["1100-1800"]],
        ]

        expected_output = [
            "MON, 27 JAN 2025", "0800-1500",
            "TUE, 28 JAN 2025", "0900-1600",
            "WED, 22 JAN 2025", "1000-1700",
            "FRI, 24 JAN 2025", "1100-1800",
        ]

        result = process_weekdays_with_dates(start_date, end_date, notam_data)
        self.assertEqual(result, expected_output)

if __name__ == "__main__":
    unittest.main()
