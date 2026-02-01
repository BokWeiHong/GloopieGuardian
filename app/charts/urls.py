from django.urls import path
from .views import charts_view

urlpatterns = [
    path('', charts_view, name='charts'),
]