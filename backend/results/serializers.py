from rest_framework import serializers
from django.conf import settings
from election import settings
from .models import PollingStation, DRForm, User, Report, AbstractUser, Agent, NupNews
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.utils import timezone
import math

class PollingStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollingStation
        fields = '__all__'

class DRFormUploadSerializer(serializers.ModelSerializer):
    # Accepts either polling station ID or station_id string
    polling_station = serializers.CharField()

    class Meta:
        model = DRForm
        fields = ['polling_station', 'image', 'video', 'sha256_hash', 'totals', 'gps']

    def validate_polling_station(self, value):
        # Try to match station by ID or by station_id
        try:
            # If the frontend sent a numeric ID, this will work
            if value.isdigit():
                return PollingStation.objects.get(pk=int(value))
            # Otherwise try to match by station_id or name
            return PollingStation.objects.get(station_id=value)
        except PollingStation.DoesNotExist:
            try:
                return PollingStation.objects.get(name=value)
            except PollingStation.DoesNotExist:
                raise serializers.ValidationError("Polling station not found")

    def create(self, validated_data):
        return DRForm.objects.create(**validated_data)

class DRFormPublicSerializer(serializers.ModelSerializer):
    polling_station = PollingStationSerializer(read_only=True)
    verified_by = serializers.StringRelatedField()

    class Meta:
        model = DRForm
        fields = ('id', 'polling_station', 'image', 'sha256_hash', 'totals', 'timestamp', 'verified', 'verified_by')
    

class DRFormSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.StringRelatedField(read_only=True)
    verified_by = serializers.StringRelatedField(read_only=True)
    polling_station = PollingStationSerializer(read_only=True)  # ✅ nested, not slug
    polling_station_id = serializers.PrimaryKeyRelatedField(
        queryset=PollingStation.objects.all(),
        source='polling_station',
        write_only=True
    )

    district = serializers.SerializerMethodField()
    sub_county = serializers.SerializerMethodField()
    parish = serializers.SerializerMethodField()

    total_votes = serializers.SerializerMethodField()
    agent_name = serializers.SerializerMethodField()
    agent_contact = serializers.SerializerMethodField()

    image = serializers.ImageField(required=False, allow_null=True)
    video = serializers.FileField(required=False, allow_null=True)
    verified = serializers.BooleanField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)

    class Meta:
        model = DRForm
        fields = '__all__'

    def get_district(self, obj):
        return getattr(obj.polling_station, "district", None)

    def get_sub_county(self, obj):
        return getattr(obj.polling_station, "constituency", None)

    def get_parish(self, obj):
        return getattr(obj.polling_station, "name", None)

    def get_total_votes(self, obj):
        try:
            return sum(obj.totals.values()) if obj.totals else 0
        except Exception:
            return 0

    def get_agent_name(self, obj):
        return getattr(obj.uploaded_by, "username", None)

    def get_agent_contact(self, obj):
        return getattr(obj.uploaded_by, "email", None)

    def validate(self, data):
        image = data.get("image")
        video = data.get("video")

        if not image and not video:
            raise serializers.ValidationError("Either image or video must be provided.")

        if image and image.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Image file too large (max 10MB).")

        if video and video.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("Video file too large (max 50MB).")

        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")

        if instance.image:
            representation["image"] = (
                request.build_absolute_uri(instance.image.url)
                if request
                else f"{settings.MEDIA_URL}{instance.image}"
            )

        if instance.video:
            representation["video"] = (
                request.build_absolute_uri(instance.video.url)
                if request
                else f"{settings.MEDIA_URL}{instance.video}"
            )

        return representation


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'is_agent']

class ReportSerializer(serializers.ModelSerializer):
    reported_by = serializers.StringRelatedField(read_only=True)
    dr_form = DRFormSerializer(read_only=True)

    class Meta:
        model = Report
        fields = '__all__'

class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = '__all__'

class AgentRegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Agent
        fields = ["username", "password", "polling_station", "phone_number", "id_number"]

    def create(self, validated_data):
        username = validated_data.pop("username")
        password = validated_data.pop("password")
        user = User.objects.create_user(username=username, password=password)
        agent = Agent.objects.create(user=user, **validated_data)
        return agent
    
class NupNewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NupNews
        fields = '__all__'