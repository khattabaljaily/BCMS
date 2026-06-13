from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('',                         views.appointment_list,   name='list'),
    path('calendar/',                views.calendar_view,      name='calendar'),
    path('calendar/events/',         views.calendar_events,    name='calendar_events'),
    path('save/',                    views.appointment_save,   name='save'),
    path('<int:pk>/status/',         views.appointment_status, name='status'),
    path('<int:pk>/delete/',         views.appointment_delete, name='delete'),
]
