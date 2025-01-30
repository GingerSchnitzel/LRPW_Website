import unittest
from token_processor_days import process_tokens

class TestProcessTokens(unittest.TestCase):

    
    def test_process_tokens_with_days(self):
        """Test processing tokens with day names."""
 
        tokens = ["MON", "TUE", "1200-1800"]
        start_date = "250101"
        end_date =  "250131"
        expected_output = [("MON", ["1200-1800"]), ("TUE", ["1200-1800"])]

        result = process_tokens(tokens, start_date, end_date)
        self.assertEqual(result, expected_output)


    def test_process_tokens_with_date_range(self):
        """Test processing tokens with a date range."""
       
        tokens = ["FRI", "10 JAN 2025","0800-1200"]
        start_date = "250101"
        end_date =  "250131"
        expected_output = [("FRI, 10 JAN 2025", ["0800-1200"])]

        result = process_tokens(tokens, start_date, end_date)
        self.assertEqual(result, expected_output)


    def test_process_tokens_with_different_time_range(self):
        """Test that repetitive day tokens with different time ranges are not deleted"""
        
        tokens = ["FRI","0800-1300","FRI", "10 JAN 2025","0800-1200"]
        start_date = "250101"
        end_date =  "250131"
        expected_output = [("FRI", ["0800-1300"]),("FRI, 10 JAN 2025", ["0800-1200"])]

        result = process_tokens(tokens, start_date, end_date)
        self.assertEqual(result, expected_output)

    def test_empty_tokens(self):
        """Test that an empty list of tokens returns an empty list."""
        
        start_date = "250101"
        end_date =  "250131"
        tokens = []
        expected_output = []

        result = process_tokens(tokens, start_date, end_date)
        self.assertEqual(result, expected_output)

if __name__ == '__main__':
    unittest.main()

'''
([Day.MON], ["0800-1300"]),
([Day.WED], ["CLSD"]),
(["FRI, 10 JAN 2025"], ["0800-1200"]),
(["SUN, 12 JAN 2025", Day.MON], ["CLSD"]),
(["TUE, 14 JAN 2025", "WED, 15 JAN 2025", "THU, 16 JAN 2025"], ["0800-1600"]),
([Day.SAT, Day.SUN], ["CLSD"]),
([Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI, Day.SAT, Day.SUN, Day.MON], ["0800-1300"]),
(["MON, 30 DEC 2024", "TUE, 31 DEC 2024", "WED, 01 JAN 2025","THU, 02 JAN 2025"], ["CLSD"]),
(["TUE, 31 DEC 2024", "WED, 01 JAN 2025","THU, 02 JAN 2025"], ["0800-1200"])
'''