from parse_NOTAM_content import parse_NOTAM_content

import unittest
from datetime import datetime
from unittest.mock import patch


class TestParseNOTAMContent(unittest.TestCase):

    def setUp(self):
        # Set up any necessary data for the tests
        self.start_date = "250131"
        self.end_date = "250210"

    def test_parse_NOTAM_content_valid(self):
        content = "TEMPORARY CHANGE OF AD ADMINISTRATION OPS HOURS AS FLW: FRI, 31 JAN: 0800-1500 SAT - TUE: CLSD WED, 05 FEB: 0800-1300 THU, 06 FEB: 0800-1300 FRI, 07 FEB: 0800-1300 SAT, 08 FEB: CLSD SUN, 09 FEB: CLSD MON, 10 FEB: 0800-1300) "
        expected_output = [
             "FRI, 31 JAN 2025", "0800-1500",
             "SAT, 01 FEB 2025", "CLSD",
             "SUN, 02 FEB 2025", "CLSD",
             "MON, 03 FEB 2025", "CLSD",
             "TUE, 04 FEB 2025", "CLSD",
             "WED, 05 FEB 2025", "0800-1300",
             "THU, 06 FEB 2025", "0800-1300",
             "FRI, 07 FEB 2025", "0800-1300",
             "SAT, 08 FEB 2025", "CLSD",
             "SUN, 09 FEB 2025", "CLSD",
             "MON, 10 FEB 2025", "0800-1300" 
        ]


        result = parse_NOTAM_content(self.start_date, self.end_date, content)
        self.assertEqual(result, expected_output)

    def test_parse_NOTAM_content_empty_content(self):
        content = ""
        expected_output = []

        result = parse_NOTAM_content(self.start_date, self.end_date, content)
        self.assertEqual(result, expected_output)

    @patch('token_processor_days.process_tokens')
    @patch('token_processor_dates.process_weekdays_with_dates')
    def test_parse_NOTAM_content_error_handling(self, mock_process_weekdays, mock_process_tokens):
        content = "Invalid content"
        mock_process_tokens.side_effect = ValueError("Invalid tokens")
        
        result = parse_NOTAM_content(self.start_date, self.end_date, content)
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()

