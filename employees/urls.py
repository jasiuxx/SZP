# employees/urls.py
from django.urls import path
from .views import EmployeeBelbinTest
from .views import belbin_results_view

urlpatterns = [
    path('belbin-test/', EmployeeBelbinTest.as_view(), name='belbin_test'),
    path('belbin-results/', belbin_results_view, name='belbin_results'),
]
