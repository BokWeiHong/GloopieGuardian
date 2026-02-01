from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.apps import apps
import json

from kismet.models import Scan

@login_required
def api_tester_view(request):
    return render(request, 'api_tester/api_tester.html')

# Updated Schema to include new mapping and metadata fields
FILTER_SCHEMA = {
    "Device": {
        "label": "Devices",
        "groups": {
            "Identity": [
                "devmac", "type", "manufacturer", "is_ap", "is_client"
            ],
            "Wireless": [
                "ssid", "channel", "encryption", "phyname"
            ],
            "Signal": [
                "strongest_signal", "avg_signal"
            ],
            "Traffic": [
                "bytes_data", "packets_seen", "clients_count"
            ],
            "Location": [
                "avg_lat", "avg_lon", "min_lat", "min_lon", "max_lat", "max_lon"
            ],
            "Time": [
                "first_time", "last_time"
            ]
        }
    },

    "Client": {
        "label": "Clients",
        "groups": {
            "Identity": [
                "client_mac", "bssid", "bssid_key", "is_associated", "client_type"
            ],
            "Traffic": [
                "datasize", "num_retries"
            ],
            "Location": [
                "last_lat", "last_lon"
            ],
            "Time": [
                "first_time", "last_time"
            ]
        }
    },

    "Packet": {
        "label": "Packets",
        "groups": {
            "MAC": [
                "sourcemac", "destmac", "transmac"
            ],
            "Radio": [
                "frequency", "signal", "datarate"
            ],
            "Location": [
                "lat", "lon", "alt"
            ],
            "Time": [
                "timestamp"
            ]
        }
    },

    "Alert": {
        "label": "Alerts",
        "groups": {
            "Info": [
                "header", "devmac"
            ],
            "Time": [
                "timestamp"
            ]
        }
    }
}

@login_required
@require_GET
def filter_schema(request):
    return JsonResponse(FILTER_SCHEMA, safe=True)

def get_model(model_name):
    try:
        return apps.get_model("kismet", model_name)
    except LookupError:
        return None

@login_required
@require_POST
def fetch_filtered_data(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body")

    scan_id = payload.get("scan_id")
    tables = payload.get("tables")

    if not scan_id or not tables:
        return HttpResponseBadRequest("scan_id and tables are required")

    if not Scan.objects.filter(id=scan_id).exists():
        return HttpResponseBadRequest("Invalid scan_id")

    response = {}

    for table_name, columns in tables.items():
        model = get_model(table_name)
        if not model:
            continue

        schema = FILTER_SCHEMA.get(table_name)
        if not schema:
            continue

        allowed_columns = set()
        for group_cols in schema["groups"].values():
            allowed_columns.update(group_cols)

        valid_columns = [c for c in columns if c in allowed_columns]
        if not valid_columns:
            continue

        # Use select_related if querying Clients to optimize AP lookups
        queryset = model.objects.filter(scan_id=scan_id)
        
        # Limit to 5000 records for performance
        data = list(queryset.values(*valid_columns)[:5000])

        response[table_name] = data

    return JsonResponse(response)