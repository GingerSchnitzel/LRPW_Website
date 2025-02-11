from django.db import models

class NOTAM_model(models.Model):

    series = models.CharField(max_length=1)
    number = models.IntegerField()
    year = models.IntegerField()
    notam_text = models.TextField()
    purpose = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.CharField(max_length=6)
    start_hour = models.CharField(max_length=4, null=True, blank=True)  # Format HHMM
    end_date = models.CharField(max_length=6)
    end_hour = models.CharField(max_length=4, null=True, blank=True)  # Format HHMM
    schedule = models.JSONField(null=True, blank=True)  # Stores schedule as a dictionary

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('series', 'number', 'year')  # Ensures uniqueness for each NOTAM
        verbose_name = "NOTAM model"  # Singular form
        verbose_name_plural = "NOTAM models"  # Plural form

    def __str__(self):
        return f"NOTAM {self.series}{self.number}/{self.year} - {self.purpose}"
