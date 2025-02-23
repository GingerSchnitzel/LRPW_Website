import unittest
from eet_time_converter import convert_schedule_to_eet

class TestScheduleConversion(unittest.TestCase):

    def test_convert_schedule_to_eet(self):
        # Test case 1: Basic schedule with a single date and time range
        schedule_1 = [
            "TUE, 18 FEB 2025", "0900-1200", "1300-1400", 
            "WED, 19 FEB 2025", "0800-1100"
        ]
        expected_1 = [
            ["Tue, 18.02.2025", "11:00 - 14:00", "15:00 - 16:00"],
            ["Wed, 19.02.2025", "10:00 - 13:00"]
        ]
        self.assertEqual(convert_schedule_to_eet(schedule_1), expected_1)

        # Test case 2: Schedule with a "CLSD" entry
        schedule_2 = [
            "TUE, 18 FEB 2025", "CLSD", 
            "WED, 19 FEB 2025", "0800-1100"
        ]
        expected_2 = [
            ["Tue, 18.02.2025", "CLSD"],
            ["Wed, 19.02.2025", "10:00 - 13:00"]
        ]
        self.assertEqual(convert_schedule_to_eet(schedule_2), expected_2)

        # Test case 3: Multiple time ranges on the same day
        schedule_3 = [
            "TUE, 18 FEB 2025", "0900-1200", "1300-1500",
            "WED, 19 FEB 2025", "0800-1100"
        ]
        expected_3 = [
            ["Tue, 18.02.2025", "11:00 - 14:00", "15:00 - 17:00"],
            ["Wed, 19.02.2025", "10:00 - 13:00"]
        ]
        self.assertEqual(convert_schedule_to_eet(schedule_3), expected_3)

        # Test case 4: Empty schedule (edge case)
        schedule_4 = []
        expected_4 = []
        self.assertEqual(convert_schedule_to_eet(schedule_4), expected_4)

        # Test case 5: Schedule with a mix of "CLSD" and time ranges
        schedule_5 = [
            "TUE, 18 FEB 2025", "CLSD", 
            "WED, 19 FEB 2025", "0800-1100", 
            "THU, 20 FEB 2025", "0900-1200"
        ]
        expected_5 = [
            ["Tue, 18.02.2025", "CLSD"],
            ["Wed, 19.02.2025", "10:00 - 13:00"],
            ["Thu, 20.02.2025", "11:00 - 14:00"]
        ]
        self.assertEqual(convert_schedule_to_eet(schedule_5), expected_5)

        schedule_6 = ['THU, 01 JUN 2023', '0400-1200', 'FRI, 02 JUN 2023', '0400-1200', 'MON, 05 JUN 2023', '0400-1200']
        expected_6 = [
            ["Thu, 01.06.2023", "07:00 - 15:00"],
            ["Fri, 02.06.2023", "07:00 - 15:00"],
            ["Mon, 05.06.2023", "07:00 - 15:00"]
        ]
        self.assertEqual(convert_schedule_to_eet(schedule_6), expected_6)

if __name__ == '__main__':
    unittest.main()
