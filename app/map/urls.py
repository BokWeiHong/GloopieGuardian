from django.urls import path
from .views import map_view, api_aps, api_monitoring_path, api_client_graph

urlpatterns = [
    path('', map_view, name='map'),
    path('api/aps/', api_aps, name='api_aps'),
    path('api/monitoring-path/', api_monitoring_path, name='api_monitoring_path'),
    path('api/client-graph/', api_client_graph, name='api_client_graph'),
]