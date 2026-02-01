from django.urls import path
from .views import api_tester_view, filter_schema, fetch_filtered_data

urlpatterns = [
    path('', api_tester_view, name='api_tester'),
    path("schema/tables/", filter_schema),
    path("data/fetch/", fetch_filtered_data),

]