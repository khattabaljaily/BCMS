from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Public store (single page: booking + products)
    path('<slug:slug>/', views.store_home, name='home'),

    # Staff management
    path('manage/bookings/',          views.bookings_list,  name='bookings'),
    path('manage/bookings/<int:pk>/', views.booking_action, name='booking_action'),
    path('manage/orders/',            views.orders_list,    name='orders'),
]
