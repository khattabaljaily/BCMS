from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('settings/', views.settings, name='settings'),
    path('', views.dashboard, name='home'),
    path('sw.js', views.service_worker, name='sw'),
    path('manifest.json', views.manifest, name='manifest'),
    path('notifications/feed/', views.notifications_feed, name='notifications_feed'),
    path('notifications/<int:pk>/read/', views.notification_read, name='notification_read'),
    path('notifications/read-all/', views.notifications_read_all, name='notifications_read_all'),
    path('store/slug-check/', views.store_slug_check, name='store_slug_check'),

    # Support tickets
    path('support/',           views.center_support,        name='support'),
    path('support/new/',       views.center_support_create, name='support_create'),
    path('support/<int:pk>/',  views.center_support_detail, name='support_detail'),

    # Pricing & subscription
    path('pricing/',      views.pricing_view,      name='pricing'),
    path('about/',        views.about_view,         name='about'),
    path('subscription/', views.subscription_view, name='subscription'),
]
