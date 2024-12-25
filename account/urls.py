from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register_employee'),
    path('login/', LoginView.as_view(template_name='account/login.html'), name='login'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('employer-profile/', views.employer_profile, name='employer_profile'),  # Nowa ścieżka
]
