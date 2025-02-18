from django.db import models
from datetime import datetime

class NOTAM_model(models.Model):
    series = models.CharField(max_length=1)
    number = models.IntegerField()
    year = models.IntegerField()
    notam_RAW_text = models.TextField()
    ad_open = models.BooleanField(default=False)  # Replaced 'purpose' with 'ad_open'
    start_date = models.CharField(max_length=6)
    start_hour = models.CharField(max_length=4, null=True, blank=True)  # Format HHMM
    end_date = models.CharField(max_length=6)
    end_hour = models.CharField(max_length=4, null=True, blank=True)  # Format HHMM
    schedule = models.JSONField(null=True, blank=True)  # Stores schedule as a dictionary

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    replaced = models.BooleanField(default=False)  # Marks if the NOTAM was replaced
    replaced_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replacing_notams')

    class Meta:
        unique_together = ('series', 'number', 'year')  # Ensures uniqueness for each NOTAM
        verbose_name = "NOTAM model"  # Singular form
        verbose_name_plural = "NOTAM models"  # Plural form

    def __str__(self):
        status = "Replaced" if self.replaced else ("Active" if self.is_active() else "Inactive")
        return f"NOTAM {self.series} - {status}"


    def is_active(self):
        """
        Checks if the NOTAM is currently active based on today's date.
        """
        today = datetime.now().date().strftime('%y%m%d')
        return self.end_date < today 
