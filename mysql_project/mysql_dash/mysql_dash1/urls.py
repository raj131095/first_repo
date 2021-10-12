from django.urls import path

from . import views
import mysql_dash1.plotly_app
urlpatterns = [
    path('', views.index, name='index'),
]