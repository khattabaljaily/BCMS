from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('',                      views.client_list,   name='list'),
    path('<int:pk>/',             views.client_detail, name='detail'),
    path('save/',                 views.client_save,   name='save'),
    path('<int:pk>/delete/',      views.client_delete, name='delete'),
]
