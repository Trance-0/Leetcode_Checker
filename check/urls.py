"""
Mapping the url requrest

This file maps the url requrest from member app and share it
"""

from django.urls import path
from . import views
urlpatterns = [
    path('', views.load_benchmark, name='load_benchmark'),
]