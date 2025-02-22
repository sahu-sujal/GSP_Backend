from django.urls import path
from . import views

urlpatterns = [
    path('login', views.admin_login, name='admin_login'),
    path('register', views.admin_register, name='admin_register'),
    path('protected', views.protected_route, name='protected_route'),
]
