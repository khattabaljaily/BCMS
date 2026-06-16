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

    # السلف
    path('advances/', views.advance_list, name='advances'),
    path('advances/new/', views.advance_create, name='advance_create'),
    path('advances/<int:pk>/cancel/', views.advance_cancel, name='advance_cancel'),

    # رواتب فريق الخدمة
    path('salaries/', views.salary_list, name='salary_list'),
    path('salaries/new/', views.salary_create, name='salary_create'),
    path('salaries/<int:pk>/', views.salary_detail, name='salary_detail'),
    path('salaries/<int:pk>/pay/', views.salary_pay, name='salary_pay'),
    path('salaries/<int:pk>/cancel/', views.salary_cancel, name='salary_cancel'),

    # سلف الموظفين
    path('user-advances/', views.user_advance_list, name='user_advances'),
    path('user-advances/new/', views.user_advance_create, name='user_advance_create'),
    path('user-advances/<int:pk>/cancel/', views.user_advance_cancel, name='user_advance_cancel'),

    # رواتب الموظفين
    path('user-salaries/', views.user_salary_list, name='user_salary_list'),
    path('user-salaries/new/', views.user_salary_create, name='user_salary_create'),
    path('user-salaries/<int:pk>/', views.user_salary_detail, name='user_salary_detail'),
    path('user-salaries/<int:pk>/pay/', views.user_salary_pay, name='user_salary_pay'),
    path('user-salaries/<int:pk>/cancel/', views.user_salary_cancel, name='user_salary_cancel'),

    # الحوافز والخصومات
    path('incentives/', views.incentive_list, name='incentives'),
    path('incentives/new/', views.incentive_create, name='incentive_create'),
    path('incentives/<int:pk>/cancel/', views.incentive_cancel, name='incentive_cancel'),
]
