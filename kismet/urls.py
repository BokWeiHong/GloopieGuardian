from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScanViewSet, DeviceViewSet, DataSourceViewSet, AlertViewSet, PacketViewSet, ClientViewSet

router = DefaultRouter()
router.register(r'scans', ScanViewSet)
router.register(r'devices', DeviceViewSet)
router.register(r'datasources', DataSourceViewSet)
router.register(r'alerts', AlertViewSet)
router.register(r'packets', PacketViewSet)
router.register(r'clients', ClientViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
