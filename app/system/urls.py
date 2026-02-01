from django.urls import path
from .views import system_view, system_status

urlpatterns = [
    path('', system_view, name='system'),
    path('status/', system_status, name='status'),
]