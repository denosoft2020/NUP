from django.contrib import admin
from .models import PollingStation, DRForm

# Register your models here.

@admin.register(PollingStation)
class PollingStationAdmin(admin.ModelAdmin):
    list_display = ('station_id', 'name', 'district', 'constituency')

@admin.register(DRForm)
class DRFormAdmin(admin.ModelAdmin):
    list_display = ('polling_station', 'timestamp', 'uploaded_by', 'verified')
    readonly_fields = ('sha256_hash', 'timestamp')