import os
import json
import sqlite3
from django.db import transaction
from datetime import datetime
from django.utils import timezone
from .models import (
    Scan, Device, DeviceData, Packet,
    DataSource, Alert, Client
)

def kismet_ts_to_datetime(ts_sec, ts_usec=0):
    if ts_sec is None:
        return None
    try:
        # Kismet timestamps are Unix epoch
        naive = datetime.fromtimestamp(ts_sec + (ts_usec or 0) / 1_000_000)
        return timezone.make_aware(naive, timezone.get_default_timezone())
    except Exception:
        return None

def safe_json_load(val):
    """Safely parse JSON strings or return dict if already parsed."""
    if not val:
        return {}
    if isinstance(val, dict):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return {}

def extract_latlon(block):
    if not block:
        return (None, None)
    point = block.get("kismet.common.location.geopoint")
    if isinstance(point, list) and len(point) == 2:
        return (point[1], point[0])  # lat, lon
    return (None, None)

def parse_clients(scan, device, device_json):
    """
    Creates mapping in the Client table from both AP and Client perspectives.
    """
    dot11 = device_json.get("dot11.device", {})
    
    # 1. Perspective: This device is an AP. Map its associated clients.
    # The key is the client MAC, value is the internal Kismet key.
    associated_map = dot11.get("dot11.device.associated_client_map", {})
    for client_mac, client_key in associated_map.items():
        Client.objects.update_or_create(
            scan=scan,
            device=device,  # The AP
            client_mac=client_mac,
            defaults={
                "bssid": device.devmac,
                "is_associated": True,
                "client_type": "Associated",
                "client_json": {"kismet_key": client_key}
            }
        )

    # 2. Perspective: This device is a Client. Map the AP it is talking to.
    client_map = dot11.get("dot11.device.client_map", {})
    for _, client_data in client_map.items():
        loc = client_data.get("dot11.client.location", {})
        last_lat, last_lon = extract_latlon(loc.get("kismet.common.location.last"))
        
        target_bssid = client_data.get("dot11.client.bssid")
        if not target_bssid or target_bssid == "00:00:00:00:00:00":
            continue

        Client.objects.update_or_create(
            scan=scan,
            device=device,  # The Client
            client_mac=device.devmac,
            defaults={
                "bssid": target_bssid,
                "bssid_key": client_data.get("dot11.client.bssid_key"),
                "client_type": client_data.get("dot11.client.type"),
                "decrypted": bool(client_data.get("dot11.client.decrypted", 0)),
                "datasize": client_data.get("dot11.client.datasize", 0),
                "num_retries": client_data.get("dot11.client.num_retries", 0),
                "first_time": kismet_ts_to_datetime(client_data.get("dot11.client.first_time")),
                "last_time": kismet_ts_to_datetime(client_data.get("dot11.client.last_time")),
                "last_lat": last_lat,
                "last_lon": last_lon,
                "client_json": client_data,
            }
        )

def import_kismet_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} does not exist")

    with sqlite3.connect(file_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # 1. Create Scan record
        scan, _ = Scan.objects.get_or_create(
            name=os.path.basename(file_path),
            defaults={"file_path": file_path}
        )

        # 2. Import Devices
        cur.execute("SELECT * FROM devices")
        rows = cur.fetchall()
        for row in rows:
            d_json = safe_json_load(row['device'])

            signal_data = d_json.get("kismet.device.base.signal", {})
            dot11 = d_json.get("dot11.device", {})

            avg_signal = signal_data.get("kismet.common.signal.avg_signal", None)
            last_signal = signal_data.get("kismet.common.signal.last_signal", None)

            packets_seen = d_json.get("kismet.device.base.packets", 0)

            assoc_map = dot11.get("dot11.device.associated_client_map", {})
            clients_count = len(assoc_map) if assoc_map else 0

            is_ap = row['type'] == "Wi-Fi AP"
            is_client = row['type'] == "Wi-Fi Client"
            probes = dot11.get("dot11.device.probed_ssid_map", [])
            advertised = dot11.get("dot11.device.advertised_ssid_map", [])

            with transaction.atomic():
                device, _ = Device.objects.update_or_create(
                    scan=scan,
                    devkey=row['devkey'],
                    defaults={
                        "phyname": row['phyname'],
                        "devmac": row['devmac'],
                        "type": row['type'],
                        "is_ap": is_ap,
                        "is_client": is_client,

                        "strongest_signal": row['strongest_signal'],
                        "avg_signal": avg_signal,
                        "last_signal": last_signal,

                        "first_time": kismet_ts_to_datetime(row['first_time']),
                        "last_time": kismet_ts_to_datetime(row['last_time']),
                        "min_lat": row['min_lat'], "min_lon": row['min_lon'],
                        "max_lat": row['max_lat'], "max_lon": row['max_lon'],
                        "avg_lat": row['avg_lat'], "avg_lon": row['avg_lon'],
                        "bytes_data": row['bytes_data'],

                        "packets_seen": packets_seen,
                        "clients_count": clients_count,

                        "ssid": d_json.get("kismet.device.base.name"),
                        "channel": d_json.get("kismet.device.base.channel"),
                        "encryption": d_json.get("kismet.device.base.crypt"),
                        "manufacturer": d_json.get("kismet.device.base.manuf"),
                        "probed_ssids": probes,
                        "advertised_ssids": advertised,
                        "device_json": d_json,
                    }
                )

                if row['type'] in ["Wi-Fi AP", "Wi-Fi Client", "Wi-Fi Bridged"]:
                    parse_clients(scan, device, d_json)

        # 3. DataSources
        cur.execute("SELECT * FROM datasources")
        for row in cur.fetchall():
            ds_json = safe_json_load(row['json'])
            DataSource.objects.update_or_create(
                uuid=row['uuid'],
                defaults={
                    "scan": scan,
                    "typestring": row['typestring'],
                    "definition": row['definition'],
                    "name": row['name'],
                    "interface": row['interface'],
                    "packet_count": ds_json.get("kismet.datasource.packets", 0),
                    "error_count": ds_json.get("kismet.datasource.errors", 0),
                    "json": ds_json,
                }
            )

        # 4. Packets (Bulk Create for Speed)
        cur.execute("SELECT * FROM packets")
        packet_rows = cur.fetchall()
        packet_objs = []
        for r in packet_rows:
            # Match back to device in memory or db
            dev = Device.objects.filter(scan=scan, devkey=r['devkey']).first()
            packet_objs.append(Packet(
                scan=scan, device=dev, ts_sec=r['ts_sec'], ts_usec=r['ts_usec'],
                timestamp=kismet_ts_to_datetime(r['ts_sec'], r['ts_usec']),
                sourcemac=r['sourcemac'], destmac=r['destmac'], transmac=r['transmac'],
                frequency=r['frequency'], signal=r['signal'], datarate=r['datarate'],
                packet_len=r['packet_len'], lat=r['lat'], lon=r['lon'],
                datasource=r['datasource'], phyname=r['phyname']
            ))
            if len(packet_objs) >= 500:
                Packet.objects.bulk_create(packet_objs)
                packet_objs = []
        Packet.objects.bulk_create(packet_objs)

        # 5. Alerts
        cur.execute("SELECT * FROM alerts")
        for r in cur.fetchall():
            Alert.objects.create(
                scan=scan, timestamp=kismet_ts_to_datetime(r['ts_sec'], r['ts_usec']),
                devmac=r['devmac'], header=r['header'], json=safe_json_load(r['json'])
            )
        
        # 6. Data
        cur.execute("SELECT * FROM data")
        for r in cur.fetchall():
            Data.objects.create(
                scan=scan, timestamp=kismet_ts_to_datetime(r['ts_sec'], r['ts_usec']),
                devkey=r['devkey'], data=r['data']
            )

    return scan