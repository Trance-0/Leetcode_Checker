"""
Mapping the url requrest

This file maps the url requrest from member app and share it
"""

from django.urls import path
from . import views
urlpatterns = [
    path('', views.get_benchmark, name='benchmark'),
    path('get_ac_data', views.get_ac_data, name='get_ac_data'),
    path('get_schedule_data', views.get_schedule_data, name='get_schedule_data'),
]