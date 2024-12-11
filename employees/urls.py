from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('register/', views.register_employee, name='register_employee'),
    path('', LoginView.as_view(template_name='employees/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', views.employee_profile, name='profile'),
]
