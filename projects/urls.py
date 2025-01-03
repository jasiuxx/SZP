from django.urls import path
from . import views
from .views import  project_list, ProjectCreateView

urlpatterns = [
    path('create/', ProjectCreateView.as_view(), name='create_project'),
    path('', project_list, name='project_list'),
    path('edit/<int:project_id>/', views.edit_project, name='edit_project'),
    path('delete/<int:project_id>/', views.ProjectDeleteView.as_view(), name='delete_project'),

]
