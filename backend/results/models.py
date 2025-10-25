from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# -------------------------------
# Custom User model
# -------------------------------
class User(AbstractUser):
    is_agent = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username


# -------------------------------
# Polling Station model
# -------------------------------
class PollingStation(models.Model):
    station_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    district = models.CharField(max_length=255)
    constituency = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.station_id} - {self.name}"


# -------------------------------
# Agent model
# -------------------------------
class Agent(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agent_profile")
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    district = models.CharField(max_length=255)
    constituency = models.CharField(max_length=255)
    polling_station = models.ForeignKey('PollingStation', on_delete=models.CASCADE, related_name='agents')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.polling_station})"


# -------------------------------
# DRForm model
# -------------------------------
class DRForm(models.Model):
    polling_station = models.ForeignKey(PollingStation, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='dr_forms/')
    video = models.FileField(upload_to='dr_videos/', null=True, blank=True)
    sha256_hash = models.CharField(max_length=128)
    timestamp = models.DateTimeField(auto_now_add=True)
    totals = models.JSONField(default=dict)
    verified = models.BooleanField(default=False)
    gps = models.JSONField(null=True, blank=True)
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


# -------------------------------
# Report model
# -------------------------------
class Report(models.Model):
    dr_form = models.ForeignKey(DRForm, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_made'
    )
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report on DRForm {self.dr_form.id} by {self.reported_by.username}"

# -------------------------------
class NupNews(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# -------------------------------
class Result(models.Model):
    party_choices = [
        ("NUP", "NUP"),
        ("NRM", "NRM"),
    ]

    party = models.CharField(max_length=10, choices=party_choices)
    votes = models.PositiveIntegerField(default=0)
    polling_station = models.ForeignKey(
        "PollingStation", on_delete=models.CASCADE, related_name="results"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.party} - {self.votes} votes"