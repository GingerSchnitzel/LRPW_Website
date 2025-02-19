from django.test import TestCase
from unittest.mock import patch, MagicMock
from lrpw_website.extended_views.ad_schedule import scrape_notams
from .views import merge_schedules
from .models import NOTAM_model

class NOTAMTests(TestCase):
    
    def setUp(self):
        """Setup test data for NOTAMs"""
        self.notam1 = NOTAM_model.objects.create(
            series="A",
            number=634,
            year=2025,
            ad_open= True,
            start_date="250212",
            end_date="250213",
            schedule="Wed, 12.02.2025 08:00 - 17:30\nThu, 13.02.2025 09:00 - 18:00",
            notam_RAW_text="A0634/25 NOTAMN Q)..."
        )
        
        self.notam2 = NOTAM_model.objects.create(
            series="A",
            number=635,
            year=2025,
            ad_open=True,
            start_date="250212",
            end_date="250212",
            schedule="Wed, 12.02.2025 10:00 - 19:00",
            notam_RAW_text="A0635/25 NOTAMN Q)..."
        )

    def test_merge_schedules(self):
        """Test if schedules are merged correctly"""
        schedule1 = ["Mon, 17.02.2025, 08:00 - 17:30", "Tue, 18.02.2025, 09:00 - 18:30"]
        schedule2 = ["Mon, 17.02.2025, 10:00 - 19:00"]

        merged = merge_schedules(schedule1, schedule2)

        expected_output = ["Mon, 17.02.2025, 10:00 - 19:00", "Tue, 18.02.2025, 09:00 - 18:30"]
        self.assertIn("Mon, 17.02.2025, 10:00 - 19:00", merged)
        
    '''
    def test_scrape_notams(self):
        """Test if scraping populates the database correctly"""
        scrape_notams()
        notams = NOTAM_model.objects.all()
        self.assertGreaterEqual(len(notams), 1)  # At least 1 NOTAM should be fetched

    def test_api_fetch_notams(self):
        """Test the API endpoint for fetching NOTAMs"""
        response = self.client.get("/api/fetch_notams/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("notams", response.json())
    
    '''

class ScrapeNotamsTestCase(TestCase):
    @patch("requests.Session.get")  # Mock the network request
    def test_scrape_notams(self, mock_get):
        # Mock NOTAM HTML response
        mock_html = """
        <div style="font-family:monospace; font-size:large;">
            (A0739/25 NOTAMR A0672/25
            Q) LRBB/QFAAH/IV/BO /A /000/999/4422N02556E005
            A) LRCN B) 2502170550 C) 2502242359
            E) TEMPORARY CHANGE OF AD ADMINISTRATION OPS HOURS AS FLW:
            MON, 17 FEB: CLSD
            TUE, 18 FEB: CLSD
            WED, 19 FEB: CLSD
            THU, 20 FEB: CLSD
            FRI, 21 FEB: CLSD
            SAT, 22 FEB: CLSD
            SUN, 23 FEB: CLSD
            MON, 24 FEB: CLSD)
        </div>
        """

        # Mock response object
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = mock_html.encode("utf-8")
        mock_get.return_value = mock_response

        print(NOTAM_model.objects.count())  # This should print the number of NOTAMs in the database before running the function

        # Run function
        result = scrape_notams()

        # Check database entry
        self.assertTrue(NOTAM_model.objects.exists(), "NOTAM was not saved in the database.")

        # Check function output
        self.assertEqual(result["message"], "NOTAM data processing completed.")

        # Fetch the saved NOTAM
        saved_notam = NOTAM_model.objects.first()
        self.assertEqual(saved_notam.series, "A0739/25")
        self.assertEqual(saved_notam.ad_open, True)
        self.assertEqual(saved_notam.start_date, "250217")
        self.assertEqual(saved_notam.end_date, "250224")
        
        expected_schedule = [
                         ["MON, 17 FEB 2025", "CLSD"],
                         ["TUE, 18 FEB 2025", "CLSD"],
                         ["WED, 19 FEB 2025", "CLSD"],
                         ["THU, 20 FEB 2025", "CLSD"],
                         ["FRI, 21 FEB 2025", "CLSD"],
                         ["SAT, 22 FEB 2025", "CLSD"],
                         ["SUN, 23 FEB 2025", "CLSD"],
                         ["MON, 24 FEB 2025", "CLSD"]
        ]
        self.assertEqual(saved_notam.schedule, expected_schedule)

        print("✅ scrape_notams() test passed!")

