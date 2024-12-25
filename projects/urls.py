from django.urls import path
from .views import create_project, project_list

urlpatterns = [
    path('create/', create_project, name='create_project'),
    path('', project_list, name='project_list'),
]
