from django.urls import path
from .views import services_view, get_interfaces, run_kismet, stop_kismet, kismet_logs, list_pcaps, run_webshark, stop_webshark

urlpatterns = [
    path('', services_view, name='services'),
    path("api/interfaces/", get_interfaces, name="get_interfaces"),
    path("api/run_kismet/", run_kismet, name="run_kismet"),
    path("api/stop_kismet/", stop_kismet, name="stop_kismet"),
    path("api/kismet_logs/", kismet_logs, name="kismet_logs"),

    path("api/pcaps/", list_pcaps),
    path("api/run_webshark/", run_webshark),
    path("api/stop_webshark/", stop_webshark),

]