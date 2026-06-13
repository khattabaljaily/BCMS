from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('',                         views.services_home,      name='list'),
    path('categories/',              views.category_list,      name='categories'),
    path('categories/add/',          views.category_form,      name='category_add'),
    path('categories/<int:pk>/edit/', views.category_form,      name='category_edit'),
    path('category/save/',           views.category_save,      name='category_save'),
    path('category/<int:pk>/delete/', views.category_delete,    name='category_delete'),
    path('service/save/',            views.service_save,       name='service_save'),
    path('service/<int:pk>/delete/', views.service_delete,     name='service_delete'),
]
