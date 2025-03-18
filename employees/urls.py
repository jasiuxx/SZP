# employees/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('belbin-test/', views.EmployeeBelbinTest.as_view(), name='belbin_test'),
    path('belbin-results/', views.belbin_results_view, name='belbin_results'),
    path('profile/<int:employee_id>/', views.employee_profile, name='employee_profile'),
    path('my-profile/', views.my_profile, name='my_profile'),
    
    # URL-e do zarządzania doświadczeniem
    path('experience/add/', views.add_experience, name='add_experience'),
    path('experience/edit/<int:experience_id>/', views.edit_experience, name='edit_experience'),
    path('experience/delete/<int:experience_id>/', views.delete_experience, name='delete_experience'),
]
