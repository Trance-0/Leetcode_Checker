"""
Mapping the url requrest

This file maps the url requrest from member app and share it
"""

from django.urls import path
from . import views
urlpatterns = [
    path('', views.benchmark, name='benchmark'),
    path('get_benchmark', views.get_benchmark, name='get_benchmark'),
]