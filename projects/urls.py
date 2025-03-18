from django.urls import path
from . import views
from .views import  project_list, ProjectCreateView, view_project_details, delete_message
from employees.views import employee_profile

urlpatterns = [
    path('create/', views.ProjectCreateView.as_view(), name='create_project'),
    path('list/', views.project_list, name='project_list'),
    path('delete/<int:project_id>/', views.ProjectDeleteView.as_view(), name='delete_project'),
    path('edit/<int:project_id>/', views.edit_project, name='edit_project'),
    path('employee/<int:employee_id>/', employee_profile, name='employee_profile'),
    path('details/<int:project_id>/', views.view_project_details, name='view_project_details'),
    path('projects/message/delete/<int:message_id>/', delete_message, name='delete_message'),
]
