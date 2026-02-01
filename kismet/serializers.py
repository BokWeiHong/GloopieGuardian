from rest_framework import serializers
from .models import (
    Scan, Device, DataSource, Alert, Packet, Client
)

class ScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scan
        fields = "__all__"

class DeviceSerializer(serializers.ModelSerializer):
    scan_name = serializers.CharField(source="scan.name", read_only=True)
    wigle_ref_data = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = "__all__"

class DataSourceSerializer(serializers.ModelSerializer):
    scan_name = serializers.CharField(source="scan.name", read_only=True)

    class Meta:
        model = DataSource
        fields = "__all__"

class AlertSerializer(serializers.ModelSerializer):
    scan_name = serializers.CharField(source="scan.name", read_only=True)

    class Meta:
        model = Alert
        fields = "__all__"

class PacketSerializer(serializers.ModelSerializer):
    scan_name = serializers.CharField(source="scan.name", read_only=True)

    class Meta:
        model = Packet
        fields = "__all__"

class ClientSerializer(serializers.ModelSerializer):
    scan_name = serializers.CharField(source="scan.name", read_only=True)

    class Meta:
        model = Client
        fields = "__all__"