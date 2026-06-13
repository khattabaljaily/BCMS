from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('treasury/', views.treasury_list, name='treasury_list'),
    path('treasury/<int:pk>/', views.treasury_detail, name='treasury_detail'),
    path('treasury/<int:pk>/initial-balance/', views.treasury_initial_balance, name='treasury_initial_balance'),

    path('expenses/', views.expense_list, name='expenses'),
    path('expenses/new/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),

    path('client-payments/', views.client_payments_list, name='client_payments'),
    path('client-payments/new/', views.client_payment_create, name='client_payment_create'),
    path('client-payments/<int:pk>/edit/', views.client_payment_edit, name='client_payment_edit'),
    path('client-payments/<int:pk>/delete/', views.client_payment_delete, name='client_payment_delete'),
    path('client-statement/', views.client_statement, name='client_statement'),
]
