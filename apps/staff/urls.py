from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('',              views.specialist_list,   name='list'),
    path('add/',          views.specialist_save,   name='add'),
    path('<int:pk>/edit/', views.specialist_save,  name='edit'),
    path('<int:pk>/delete/', views.specialist_delete, name='delete'),
]
