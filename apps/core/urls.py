from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('settings/', views.settings, name='settings'),
    path('', views.dashboard, name='home'),
    path('sw.js', views.service_worker, name='sw'),
    path('manifest.json', views.manifest, name='manifest'),
]
