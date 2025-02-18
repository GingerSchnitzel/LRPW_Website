from django.test import TestCase
from lrpw_website.models import NOTAM_model
from lrpw_website.views import merge_schedules, scrape_notams
from lrpw_website.extended_views.ad_schedule import scrape_notams
from datetime import date

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
        schedule1 = "Mon, 17.02.2025 08:00 - 17:30\nTue, 18.02.2025 09:00 - 18:30"
        schedule2 = "Mon, 17.02.2025 10:00 - 19:00"

        merged = merge_schedules(schedule1, schedule2)

        expected_output = "Mon, 17.02.2025 10:00 - 19:00\nTue, 18.02.2025 09:00 - 18:30"
        self.assertIn("Mon, 17.02.2025 10:00 - 19:00", merged)
        
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