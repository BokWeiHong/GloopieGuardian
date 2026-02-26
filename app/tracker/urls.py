from django.urls import path
from .views import tracker_view, start_network_scan, stop_network_scan, status_network_scan, get_wifi_map_data

urlpatterns = [
    path('', tracker_view, name='tracker'),
    path('start-scan/', start_network_scan, name='start_network_scan'),
    path('stop-scan/', stop_network_scan, name='stop_network_scan'),
    path('status-scan/', status_network_scan, name='status_network_scan'),
    path('wifi-map/', get_wifi_map_data, name='get_wifi_map_data'),
]