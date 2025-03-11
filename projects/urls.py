from django.urls import path
from . import views
from .views import  project_list, ProjectCreateView

urlpatterns = [
    path('create/', views.ProjectCreateView.as_view(), name='create_project'),
    path('list/', views.project_list, name='project_list'),
    path('delete/<int:project_id>/', views.ProjectDeleteView.as_view(), name='delete_project'),
    path('edit/<int:project_id>/', views.edit_project, name='edit_project'),
    path('test-algorithm/', views.test_algorithm_view, name='test_algorithm'),
]
