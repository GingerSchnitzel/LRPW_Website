import unittest
from tokenizer import Day, TokenType,parse_year, make_day_range, get_day, is_time_range, is_date, parse_date, get_type, generate_date_range, get_time_groups
from datetime import datetime

class TestFunctions(unittest.TestCase):
    def test_parse_year(self):
        # Test valid date strings in YYMMDD format
        self.assertEqual(parse_year("250106"), datetime(2025, 1, 6))  # 25th of January, 2025
        self.assertEqual(parse_year("230315"), datetime(2023, 3, 15))  # 15th of March, 2023
        self.assertEqual(parse_year("220501"), datetime(2022, 5, 1))   # 1st of May, 2022
        self.assertEqual(parse_year("190912"), datetime(2019, 9, 12))  # 12th of September, 2019

        # Test edge cases for dates
        self.assertEqual(parse_year("990101"), datetime(1999, 1, 1))  # 1st of January, 1999
        self.assertEqual(parse_year("000101"), datetime(2000, 1, 1))  # 1st of January, 2000

        # Test invalid date strings (this will raise a ValueError)
        with self.assertRaises(ValueError):
            parse_year("25013Z")  # Invalid month
        with self.assertRaises(ValueError):
            parse_year("25099X")  # Invalid day

    def test_make_day_range(self):
        self.assertEqual(make_day_range(Day.MON, Day.WED, "250101", "250103"), [Day.MON, Day.TUE, Day.WED])
        self.assertEqual(make_day_range(Day.FRI, Day.MON, "250102", "250104"), [Day.FRI, Day.SAT, Day.SUN, Day.MON])
        self.assertEqual(make_day_range(Day.MON, Day.MON, "250101", "250107"), [Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI, Day.SAT, Day.SUN, Day.MON])
        self.assertEqual(make_day_range(Day.INVALID, Day.MON, "250101", "250107"), [])
        self.assertEqual(make_day_range(Day.MON, Day.INVALID, "250101", "250120"), [])
        self.assertEqual(make_day_range(Day.MON, Day.MON, "250106", "250120"), [Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI, Day.SAT, Day.SUN, Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI, Day.SAT, Day.SUN, Day.MON])


    def test_get_day(self):
        self.assertEqual(get_day("MON"), Day.MON)
        self.assertEqual(get_day("SAT"), Day.SAT)
        self.assertEqual(get_day("INVALID"), Day.INVALID)

    def test_is_time_range(self):
        self.assertTrue(is_time_range("0800-1500"))
        self.assertTrue(is_time_range("0000-2359"))
        self.assertFalse(is_time_range("0800-15"))
        self.assertFalse(is_time_range("TIME-RANGE"))

    def test_is_date(self):
        self.assertTrue(is_date("10 JAN"))
        self.assertTrue(is_date("10 JAN 2025"))
        self.assertFalse(is_date("10 JANUARY"))
        self.assertFalse(is_date("10 01 2025"))

    def test_parse_date(self):
        self.assertEqual(parse_date("10 JAN"), "FRI, 10 JAN 2025")
        self.assertEqual(parse_date("10 JAN 2025"), "FRI, 10 JAN 2025")
        self.assertIsNone(parse_date("INVALID"))

    def test_get_type(self):
        self.assertEqual(get_type("MON"), TokenType.DAY)
        self.assertEqual(get_type("-"), TokenType.DASH)
        self.assertEqual(get_type("0800-1500"), TokenType.TIME_RANGE)
        self.assertEqual(get_type("CLSD"), TokenType.CLSD)
        self.assertEqual(get_type("10 JAN"), TokenType.DATE)
        self.assertEqual(get_type("10 JAN 2025"), TokenType.DATE)

        self.assertEqual(get_type("INVALID"), TokenType.INVALID)

    def test_generate_date_range(self):
        start_date = "FRI, 10 JAN 2025"
        end_date = "SUN, 12 JAN 2025"
        expected = ["FRI, 10 JAN 2025", "SAT, 11 JAN 2025", "SUN, 12 JAN 2025"]
        self.assertEqual(generate_date_range(start_date, end_date), expected)
        
        # Test invalid date range
        #self.assertEqual(generate_date_range("SUN, 12 JAN 2025", "FRI, 10 JAN 2025"), [])

    def test_get_time_groups(self):
        tokens = [
            "MON", "0800-1300", "WED", "CLSD", "10 JAN", "0800-1200", 
            "12 JAN", "MON", "CLSD", "14 JAN 2025", "-", "16 JAN 2025", "0800-1600",
            "SAT", "SUN", "CLSD", 
            "MON", "-", "MON", "0800-1300", 
            "MON", "30 DEC 2024", "-", "THU", "02 JAN 2025", "CLSD",
            "31 DEC", "-", "02 JAN", "0800-1200"
        ]
        start_date = "240101"
        end_date = "251231"
        result = get_time_groups(tokens, start_date, end_date)
        
        expected = [
        ([Day.MON], ["0800-1300"]),
        ([Day.WED], ["CLSD"]),
        (["FRI, 10 JAN 2025"], ["0800-1200"]),
        (["SUN, 12 JAN 2025", Day.MON], ["CLSD"]),
        (["TUE, 14 JAN 2025", "WED, 15 JAN 2025", "THU, 16 JAN 2025"], ["0800-1600"]),
        ([Day.SAT, Day.SUN], ["CLSD"]),
        ([Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI, Day.SAT, Day.SUN, Day.MON], ["0800-1300"]),
        (["MON, 30 DEC 2024", "TUE, 31 DEC 2024", "WED, 01 JAN 2025","THU, 02 JAN 2025"], ["CLSD"]),
        (["TUE, 31 DEC 2024", "WED, 01 JAN 2025","THU, 02 JAN 2025"], ["0800-1200"])

        ]
        self.assertEqual(result, expected)

        # Test invalid tokens
        with self.assertRaises(ValueError):
            tkn = ["INVALID", "0800-1300"]
            get_time_groups(tkn, start_date, end_date)

    def test_get_time_groups_special_cases(self):
        token =["MON","-", "TUE", "0800-1300"]
        self.assertEqual(get_time_groups(token, "250106", "250121"),
            [
               ([Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI, Day.SAT, Day.SUN, 
                 Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI, Day.SAT, Day.SUN, 
                 Day.MON, Day.TUE], ["0800-1300"])
            ]
        )
        token1 = ["MON", "-", "MON", "0800-1300"]
        self.assertEqual(get_time_groups(token1, "250106", "250120"),
            [           
            ([Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI, Day.SAT, Day.SUN, 
              Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI, Day.SAT, Day.SUN, 
              Day.MON], ["0800-1300"])
            ]  
        )

if __name__ == "__main__":
    unittest.main()