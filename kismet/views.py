from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import Scan, Device, DataSource, Alert, Packet, Client
from .serializers import (
    ScanSerializer, DeviceSerializer, DataSourceSerializer, 
    AlertSerializer, PacketSerializer, ClientSerializer
)
from django.db.models import Avg, Count, Max, Min, Sum, F
from django.db.models.functions import TruncDay, Round
from django.utils import timezone
from django.conf import settings

class ScanViewSet(viewsets.ModelViewSet):
    queryset = Scan.objects.all().order_by('-id')
    serializer_class = ScanSerializer
    pagination_class = None
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['id', 'name']

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

    def get_queryset(self, request):
        scan_ids = request.query_params.get('scan_id')
        queryset = Device.objects.all()

        if scan_ids:
            scan_ids = [int(sid) for sid in scan_ids.split(',') if sid.isdigit()]
            queryset = queryset.filter(scan_id__in=scan_ids)

        return queryset

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        total_scans = self.get_queryset(request).count()
        access_points = self.get_queryset(request).filter(type__icontains='AP').count()
        connected_clients = self.get_queryset(request).filter(type__icontains='Client').count()
        avg_signal = self.get_queryset(request).aggregate(avg_signal=Avg('strongest_signal'))['avg_signal'] or 0

        return Response({
            'total_scans': total_scans,
            'access_points': access_points,
            'connected_clients': connected_clients,
            'avg_signal': round(avg_signal, 2)
        })

    # --- Devices by Type (APs vs Clients) ---
    # Chart Type: Pie / Donut
    @action(detail=False, methods=['get'], url_path='by-type')
    def devices_by_type(self, request):
        data = list(
            self.get_queryset(request)
                .values('type')
                .annotate(count=Count('id'))
                .order_by('type')
        )
        return Response(data)

    # --- Signal Strength Distribution ---
    # Chart Type: Histogram / Bar
    @action(detail=False, methods=['get'], url_path='signal-distribution')
    def signal_distribution(self, request):
        histogram = {}
        for d in self.get_queryset(request).exclude(strongest_signal__isnull=True).values_list('strongest_signal', flat=True):
            bin_val = 5 * (d // 5)  # 5 dBm bins
            histogram[bin_val] = histogram.get(bin_val, 0) + 1
        data = [{"bin": k, "count": v} for k, v in sorted(histogram.items())]
        return Response(data)

    # --- Signal Strength Distribution ---
    # Chart Type: Pie & Bar Chart
    @action(detail=False, methods=['get'], url_path='signal-strength-distribution')
    def signal_strength_distribution(self, request):
        devices = self.get_queryset(request).exclude(strongest_signal__isnull=True)

        # Group signal into categories
        categories = {'Strong': 0, 'Medium': 0, 'Weak': 0, 'Very Weak': 0}
        for d in devices:
            s = d.strongest_signal
            if s >= -50:
                categories['Strong'] += 1
            elif s >= -70:
                categories['Medium'] += 1
            elif s >= -85:
                categories['Weak'] += 1
            else:
                categories['Very Weak'] += 1

        data = [{"category": k, "count": v} for k, v in categories.items()]
        return Response(data)

    # --- Average Signal by Manufacturer ---
    # Chart Type: Horizontal Bar
    @action(detail=False, methods=['get'], url_path='avg-signal-manufacturer')
    def avg_signal_by_manufacturer(self, request):
        data = list(
            self.get_queryset(request)
                .filter(strongest_signal__lt=0)
                .values('manufacturer', 'ssid')
                .annotate(avg_signal=Avg('strongest_signal'))
                .order_by('-avg_signal')[:10]
        )
        return Response(data)

    # --- Devices over Time ---
    # Chart Type: Line Chart
    @action(detail=False, methods=['get'], url_path='devices-over-time')
    def devices_over_time(self, request):
        data = list(
            self.get_queryset(request)
                .annotate(day=TruncDay('first_time'))
                .values('day')
                .annotate(count=Count('id'))
                .order_by('day')
        )
        return Response(data)

    # --- Geolocation Map (Device Positions) ---
    # Chart Type: Scatter / Map Overlay
    @action(detail=False, methods=['get'], url_path='geolocation')
    def geolocation(self, request):
        data = list(
            self.get_queryset(request)
                .exclude(avg_lat__isnull=True, avg_lon__isnull=True)
                .exclude(avg_lat=0, avg_lon=0)
                .values('devkey', 'avg_lat', 'avg_lon', 'strongest_signal')
        )
        return Response(data)

    # --- Channel Usage Distribution ---
    # Chart Type: Bar Chart
    @action(detail=False, methods=['get'], url_path='channel-usage')
    def channel_usage(self, request):
        data = list(
            self.get_queryset(request)
                .values('channel')
                .annotate(count=Count('id'))
                .order_by('channel')
        )
        return Response(data)

    # --- Encryption Type Distribution ---
    # Chart Type: Pie Chart
    @action(detail=False, methods=['get'], url_path='encryption-types')
    def encryption_types(self, request):
        data = list(
            self.get_queryset(request)
                .values('encryption')
                .annotate(count=Count('id'))
                .order_by('-count')
        )
        return Response(data)

    # --- Top Manufacturers by Device Count ---
    # Chart Type: Bar / Horizontal Bar
    @action(detail=False, methods=['get'], url_path='top-manufacturers')
    def top_manufacturers(self, request):
        data = list(
            self.get_queryset(request)
                .exclude(manufacturer__isnull=True)
                .values('manufacturer')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
        )
        return Response(data)

    # Table: SSIDs seen multiple times in the same area
    @action(detail=False, methods=['get'], url_path='ssid-overlap')
    def ssid_overlap(self, request):
        data = list(
            self.get_queryset(request)
                .exclude(avg_lat__isnull=True, avg_lon__isnull=True)
                .values('ssid', 'avg_lat', 'avg_lon')
                .annotate(count=Count('id'))
                .filter(count__gt=1)
                .order_by('-count')
        )
        return Response(data)

    # Line Chart / Table: Newly detected vs previously seen devices
    @action(detail=False, methods=['get'], url_path='new-vs-returning-devices')
    def new_vs_returning(self, request):
        devices = self.get_queryset(request)
        new_count = devices.filter(first_time=F('last_time')).count()
        returning_count = devices.exclude(first_time=F('last_time')).count()
        return Response({"new": new_count, "returning": returning_count})
    
    @action(detail=True, methods=['get'], url_path='wigle-lookup')
    def wigle_lookup(self, request, pk=None):
        device = self.get_object()
        if not device.devmac:
            return Response({"error": "Device has no MAC address"}, status=400)

        user = request.query_params.get("user")
        password = request.query_params.get("pass")

        if not user or not password:
            return Response({"error": "WiGLE credentials missing"}, status=400)

        response = requests.get(
            "https://api.wigle.net/api/v2/network/search",
            auth=(user, password),
            params={"netid": device.devmac}
        )

        if response.status_code == 200:
            data = response.json().get('results', [])
            return Response(data)
        else:
            return Response({
                "error": f"WiGLE API returned {response.status_code}",
                "details": response.text
            }, status=response.status_code)

class DataSourceViewSet(viewsets.ModelViewSet):
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer

    def get_queryset(self):
        queryset = DataSource.objects.all()
        scan_id = self.request.query_params.get('scan_id')
        if scan_id:
            queryset = queryset.filter(scan_id=scan_id)
        return queryset

class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer

    def get_queryset(self):
        queryset = Alert.objects.all()
        scan_id = self.request.query_params.get('scan_id')
        if scan_id:
            queryset = queryset.filter(scan_id=scan_id)
        return queryset

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        scan_id = request.query_params.get('scan_id')
        queryset = self.get_queryset()
        if scan_id:
            queryset = queryset.filter(scan_id=scan_id)

        data = list(
            queryset.values('header')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        latest_alerts = list(
            queryset.order_by('-ts_sec')[:5].values('ts_sec', 'header', 'devmac')
        )

        return Response({
            "alert_summary": data,
            "recent_alerts": latest_alerts,
        })

class PacketViewSet(viewsets.ModelViewSet):
    queryset = Packet.objects.all()
    serializer_class = PacketSerializer

    def get_queryset(self):
        queryset = Snapshot.objects.all()
        scan_id = self.request.query_params.get('scan_id')
        if scan_id:
            queryset = queryset.filter(scan_id=scan_id)
        return queryset

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def get_queryset(self):
        queryset = Client.objects.all()
        scan_id = self.request.query_params.get('scan_id')
        if scan_id:
            queryset = queryset.filter(scan_id=scan_id)
        return queryset