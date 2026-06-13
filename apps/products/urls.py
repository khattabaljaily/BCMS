from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('',                   views.product_list,    name='list'),
    path('add/',               views.product_save,    name='add'),
    path('<int:pk>/edit/',     views.product_save,    name='edit'),
    path('<int:pk>/delete/',   views.product_delete,  name='delete'),
    path('categories/',        views.category_list,   name='categories'),
    path('categories/save/',   views.category_save,   name='category_save'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    path('stock/',             views.stock_list,      name='stock'),
    path('stock/summary/',     views.stock_summary,   name='stock_summary'),

    path('purchases/',                      views.purchase_list,   name='purchase_list'),
    path('purchases/new/',                  views.purchase_create, name='purchase'),
    path('purchases/<int:pk>/',             views.purchase_detail, name='purchase_detail'),
    path('purchases/<int:pk>/edit/',        views.purchase_edit,   name='purchase_edit'),
    path('purchases/<int:pk>/cancel/',      views.purchase_cancel, name='purchase_cancel'),
    path('purchases/<int:pk>/pay/',         views.purchase_pay,    name='purchase_pay'),
]
