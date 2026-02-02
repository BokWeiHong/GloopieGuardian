from django.urls import path
from .views import tracker_view

urlpatterns = [
    path('', tracker_view, name='tracker'),
]