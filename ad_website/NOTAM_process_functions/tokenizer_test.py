import unittest
from tokenizer import Day, TokenType, make_day_range, get_day, is_time_range, is_date, parse_date, get_type, generate_date_range, get_time_groups

class TestFunctions(unittest.TestCase):
    def test_make_day_range(self):
        self.assertEqual(make_day_range(Day.MON, Day.WED), [Day.MON, Day.TUE, Day.WED])
        self.assertEqual(make_day_range(Day.FRI, Day.MON), [Day.FRI, Day.SAT, Day.SUN, Day.MON])
        self.assertEqual(make_day_range(Day.MON, Day.MON), [Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI, Day.SAT, Day.SUN, Day.MON])
        self.assertEqual(make_day_range(Day.INVALID, Day.MON), [])
        self.assertEqual(make_day_range(Day.MON, Day.INVALID), [])

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
        result = get_time_groups(tokens)
        
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
            get_time_groups(["INVALID", "0800-1300"])

if __name__ == "__main__":
    unittest.main()