from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'sysadmin'

urlpatterns = [
    path('',                         views.dashboard,    name='dashboard'),
    path('dashboard/',               views.dashboard,    name='dashboard_alt'),

    # Centers
    path('centers/',                 views.center_list,   name='center_list'),
    path('centers/add/',             views.center_add,    name='center_add'),
    path('centers/<int:pk>/',        views.center_detail, name='center_detail'),
    path('centers/<int:pk>/edit/',   views.center_edit,   name='center_edit'),
    path('centers/<int:pk>/toggle/', views.center_toggle, name='center_toggle'),
    path('centers/<int:pk>/extend/', views.center_extend, name='center_extend'),
    path('centers/<int:pk>/delete/', views.center_delete, name='center_delete'),

    # Service types
    path('service-types/',                      views.service_types,       name='service_types'),
    path('service-types/add/',                  views.service_type_save,   name='service_type_add'),
    path('service-types/<int:pk>/edit/',        views.service_type_save,   name='service_type_edit'),
    path('service-types/<int:pk>/delete/',      views.service_type_delete, name='service_type_delete'),

    # Backup & Restore
    path('backup/',                              views.backup_list,          name='backup_list'),
    path('backup/<int:pk>/',                     views.backup_detail,        name='backup_detail'),
    path('backup/<int:pk>/create/',              views.backup_create_api,    name='backup_create_api'),
    path('backup/restore/<int:backup_id>/',      views.backup_restore_api,   name='backup_restore_api'),
    path('backup/delete/<int:backup_id>/',       views.backup_delete_api,    name='backup_delete_api'),
    path('backup/download/<int:backup_id>/',     views.backup_download,      name='backup_download'),

    # Users overview
    path('users/', views.users_overview, name='users'),
]
