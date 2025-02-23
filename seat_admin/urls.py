from django.urls import path
from . import views

urlpatterns = [
    path('login', views.admin_login, name='admin_login'),
    path('register', views.admin_register, name='admin_register'),
    path('get_admin_dashboard_data', views.get_admin_dashboard_data, name='get_admin_dashboard_data'),
]
