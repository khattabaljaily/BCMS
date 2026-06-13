from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/',    views.login_view,    name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/',   views.logout_view,   name='logout'),
    path('profile/',  views.profile_view,  name='profile'),
    # User management
    path('users/',            views.user_list,   name='users'),
    path('users/add/',        views.user_save,   name='user_add'),
    path('users/<int:pk>/edit/',  views.user_save,   name='user_edit'),
    path('users/<int:pk>/delete/',views.user_delete, name='user_delete'),
    # Roles
    path('roles/',            views.role_list,   name='roles'),
    path('roles/add/',        views.role_save,   name='role_add'),
    path('roles/<int:pk>/edit/',  views.role_save,   name='role_edit'),
]
