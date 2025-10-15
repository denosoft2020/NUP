from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.

class PollingStation(models.Model):
    station_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    district = models.CharField(max_length=255)
    constituency = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.station_id} - {self.name}"

class DRForm(models.Model):
    polling_station = models.ForeignKey(PollingStation, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='dr_forms/')
    video = models.FileField(upload_to='dr_videos/', null=True, blank=True)
    sha256_hash = models.CharField(max_length=128)
    timestamp = models.DateTimeField(auto_now_add=True)
    totals = models.JSONField(default=dict)  # e.g. {"NUP": 120, "NRM": 10}
    verified = models.BooleanField(default=False)
    gps = models.JSONField(null=True, blank=True)  # store {lat, lng} only if allowed
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="uploaded_forms"
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_forms"
    )

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"DRForm {self.polling_station.station_id} @ {self.timestamp.isoformat()}"
    
class User(AbstractUser):
    is_agent = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username