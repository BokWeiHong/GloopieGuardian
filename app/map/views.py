from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from kismet.models import Device, Scan, Packet, Client
from django.db.models import Avg

@login_required
def map_view(request):
   return render(request, 'map/map.html')

def api_aps(request):
   scan_ids = request.GET.get('scan_id')

   if scan_ids:
      scan_ids = [int(x) for x in scan_ids.split(',') if x.isdigit()]
      aps = Device.objects.filter(scan_id__in=scan_ids)
   else:
      aps = Device.objects.all()

   data = [
      {
         'devkey': ap.devkey,
         'phyname': ap.phyname,
         'devmac': ap.devmac,
         'type': ap.type,
         'ssid': getattr(ap, 'ssid', None),
         'channel': getattr(ap, 'channel', None),
         'encryption': getattr(ap, 'encryption', None),
         'strongest_signal': getattr(ap, 'strongest_signal', None),
         'manufacturer': getattr(ap, 'manufacturer', None),
         'lat': getattr(ap, 'avg_lat', None),
         'lon': getattr(ap, 'avg_lon', None),
         'scan_id': ap.scan_id
      }
      for ap in aps
   ]
   return JsonResponse(data, safe=False)

def api_monitoring_path(request):
   scan_ids_raw = request.GET.get('scan_id')

   if scan_ids_raw:
      scan_ids = [int(x) for x in scan_ids_raw.split(',') if x.isdigit()]
      packets = Packet.objects.filter(scan_id__in=scan_ids)
   else:
      latest_scan = Scan.objects.order_by('-imported_at').first()
      if latest_scan:
         packets = Packet.objects.filter(scan_id=latest_scan.id)
      else:
         return JsonResponse({}, safe=False)

   averages = (
      packets.exclude(lat=0.0, lon=0.0)
      .aggregate(
         avg_lat=Avg('lat'),
         avg_lon=Avg('lon')
      )
   )

   if averages['avg_lat'] is None:
      return JsonResponse({"success": False, "error": "No valid GPS data"}, status=404)

   data = {
      'lat': averages['avg_lat'],
      'lon': averages['avg_lon'],
      'scan_id': scan_ids_raw if scan_ids_raw else latest_scan.id,
      'type': 'average_center',
      'success': True
   }

   return JsonResponse(data, safe=False)

def api_client_graph(request):
   scan_ids = request.GET.get('scan_id')

   if scan_ids:
      scan_ids = [
            int(sid) for sid in scan_ids.split(',')
            if sid.strip().isdigit()
      ]
      qs = Client.objects.filter(scan_id__in=scan_ids)
   else:
      qs = Client.objects.all()
   qs = qs.select_related('device')
   elements = []
   added_nodes = set()

   def ap_node_id(device):
      return f"ap-{device.id}"
   def client_node_id(mac):
      return f"cl-{mac}"

   for rel in qs:
      device = rel.device
      client_mac = rel.client_mac
      if not device or not client_mac:
            continue

      if not device.is_ap:
            continue
      ap_id = ap_node_id(device)
      cl_id = client_node_id(client_mac)

      if ap_id not in added_nodes:
            elements.append({
               "data": {
                  "id": ap_id,
                  "label": device.ssid or device.devmac or "UNKNOWN_AP",
                  "mac": device.devmac,
                  "type": "AP",
                  "vendor": device.manufacturer or "Unknown",
                  "channel": device.channel,
                  "encryption": device.encryption,
                  "lat": device.avg_lat or 0,
                  "lon": device.avg_lon or 0
               }
            })
            added_nodes.add(ap_id)

      if cl_id not in added_nodes:
            elements.append({
               "data": {
                  "id": cl_id,
                  "label": client_mac,
                  "mac": client_mac,
                  "type": "CLIENT",
                  "vendor": "Unknown",
                  "lat": rel.last_lat or 0,
                  "lon": rel.last_lon or 0
               }
            })
            added_nodes.add(cl_id)

      edge_type = "Associated" if rel.is_associated else "Observed"

      confidence = 0.85 if rel.is_associated else 0.35

      if rel.datasize and rel.datasize > 0:
            confidence += 0.05
      confidence = min(confidence, 1.0)
      elements.append({
            "data": {
               "id": f"edge-{device.id}-{client_mac}",
               "source": cl_id,
               "target": ap_id,
               "type": edge_type,
               "confidence": confidence,
               "datasize": rel.datasize,
               "retries": rel.num_retries,
               "decrypted": rel.decrypted,
               "last_seen": rel.last_time.isoformat() if rel.last_time else None
            }
      })
   return JsonResponse(elements, safe=False)