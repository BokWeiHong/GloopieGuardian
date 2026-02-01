from django.db import models

class Scan(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    file_path = models.CharField(max_length=255, null=True, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "scans"

    def __str__(self):
        return self.name or f"Scan {self.id}"

class Device(models.Model):
    scan = models.ForeignKey(
        Scan,
        on_delete=models.CASCADE,
        related_name="devices"
    )

    # Identity
    devkey = models.CharField(max_length=64)
    devmac = models.CharField(max_length=17, null=True, blank=True)
    phyname = models.CharField(max_length=50, null=True, blank=True)
    type = models.CharField(max_length=50, null=True, blank=True)
    
    # Association Logic Helper Flags
    is_ap = models.BooleanField(default=False, db_index=True)
    is_client = models.BooleanField(default=False, db_index=True)

    # Network info
    ssid = models.CharField(max_length=255, null=True, blank=True)
    channel = models.CharField(max_length=20, null=True, blank=True)
    encryption = models.CharField(max_length=100, null=True, blank=True)
    manufacturer = models.CharField(max_length=100, null=True, blank=True)
    
    # Wi-Fi Specifics (Parsed from JSON)
    probed_ssids = models.JSONField(null=True, blank=True)    # For Clients: SSIDs they search for
    advertised_ssids = models.JSONField(null=True, blank=True) # For APs: SSIDs they broadcast

    # Signal metrics
    strongest_signal = models.IntegerField(null=True, blank=True)
    avg_signal = models.FloatField(null=True, blank=True)
    last_signal = models.IntegerField(null=True, blank=True)

    # Observation time
    first_time = models.DateTimeField(null=True, blank=True)
    last_time = models.DateTimeField(null=True, blank=True)

    # GPS info
    min_lat = models.FloatField(null=True, blank=True)
    max_lat = models.FloatField(null=True, blank=True)
    min_lon = models.FloatField(null=True, blank=True)
    max_lon = models.FloatField(null=True, blank=True)
    avg_lat = models.FloatField(null=True, blank=True)
    avg_lon = models.FloatField(null=True, blank=True)

    # Traffic metrics
    bytes_data = models.BigIntegerField(null=True, blank=True)
    packets_seen = models.BigIntegerField(null=True, blank=True)
    clients_count = models.IntegerField(null=True, blank=True)

    # Raw Kismet JSON
    device_json = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "devices"
        indexes = [
            models.Index(fields=["scan"]),
            models.Index(fields=["devmac"]),
            models.Index(fields=["type"]),
            models.Index(fields=["avg_lat", "avg_lon"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["scan", "devkey"],
                name="unique_device_per_scan"
            )
        ]

    def __str__(self):
        return f"{self.devmac or 'Unknown'} ({self.type or 'Device'})"

class Client(models.Model):
    scan = models.ForeignKey(
        Scan,
        on_delete=models.CASCADE,
        related_name="clients"
    )

    # The 'parent' device record (usually the AP)
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="associated_clients"
    )

    # Identity of the peer
    client_mac = models.CharField(max_length=17, db_index=True)
    bssid = models.CharField(max_length=17, null=True, blank=True)
    bssid_key = models.CharField(max_length=64, null=True, blank=True)

    # Connection Status
    is_associated = models.BooleanField(default=False)
    client_type = models.CharField(max_length=50, null=True, blank=True)
    decrypted = models.BooleanField(default=False)

    # Traffic specific to this pair
    datasize = models.BigIntegerField(default=0)
    num_retries = models.IntegerField(default=0)

    # Time & Location
    first_time = models.DateTimeField(null=True, blank=True)
    last_time = models.DateTimeField(null=True, blank=True)
    last_lat = models.FloatField(null=True, blank=True)
    last_lon = models.FloatField(null=True, blank=True)

    # Raw JSON
    client_json = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "clients"
        unique_together = ("scan", "device", "client_mac")
        indexes = [
            models.Index(fields=["client_mac"]),
            models.Index(fields=["bssid"]),
        ]

    def __str__(self):
        return f"{self.client_mac} -> {self.device.devmac}"

class Packet(models.Model):
    """Individual packet records from the 'packets' table"""
    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="packets")
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name="packets")

    ts_sec = models.IntegerField(db_index=True)
    ts_usec = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(db_index=True)
    
    sourcemac = models.CharField(max_length=17, null=True, blank=True)
    destmac = models.CharField(max_length=17, null=True, blank=True)
    transmac = models.CharField(max_length=17, null=True, blank=True)
    
    frequency = models.IntegerField(null=True, blank=True)
    signal = models.IntegerField(null=True, blank=True)
    datarate = models.FloatField(null=True, blank=True)
    packet_len = models.IntegerField(null=True, blank=True)

    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    alt = models.FloatField(null=True, blank=True)

    datasource = models.CharField(max_length=50, null=True, blank=True)
    phyname = models.CharField(max_length=50, null=True, blank=True)
    packet_json = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "packets"

class DataSource(models.Model):
    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="datasources")
    uuid = models.CharField(max_length=64, unique=True)
    typestring = models.CharField(max_length=50, null=True, blank=True)
    definition = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    interface = models.CharField(max_length=50, null=True, blank=True)
    
    # Missing: stats
    packet_count = models.BigIntegerField(default=0)
    error_count = models.BigIntegerField(default=0)
    
    json = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "datasources"

class Alert(models.Model):
    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="alerts")
    timestamp = models.DateTimeField(db_index=True)
    devmac = models.CharField(max_length=17, null=True, blank=True)
    header = models.CharField(max_length=200, null=True, blank=True)
    json = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "alerts"

class DeviceData(models.Model):
    """Temporal data from the 'data' table (Signal snapshots, etc)"""
    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="device_data")
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(db_index=True)
    devmac = models.CharField(max_length=17, null=True, blank=True)
    type = models.CharField(max_length=50, null=True, blank=True)
    json = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "data"