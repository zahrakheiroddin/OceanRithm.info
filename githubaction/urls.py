from django.urls import path
from . import  views

urlpatterns = [
       # Dashboard and GitHub Config
    path('', views.dashboard_view, name='githubaction_dashboard'),
    path('github-config/', views.github_config_view, name='github_config'),
    
    # Repository management
    path('repository-choice/', views.repository_choice_view, name='repository_choice'),
    path('new-repository/', views.new_repository_view, name='new_repository'),
    path('existing-repository/', views.existing_repository_view, name='existing_repository'),
    path('repository/<int:repo_id>/', views.repository_detail_view, name='repository_detail'),
    # Handle empty path for browse
    path('repository/<int:repo_id>/browse/', views.repository_browse_view, name='repository_browse_root'),
    # URL for browsing nested directories
    path('repository/<int:repo_id>/browse/<path:path>/', views.repository_browse_view, name='repository_browse'),
    # ✅ Add this line for delete
    path('delete-repository/<int:repo_id>/', views.delete_repository_view, name='repository_delete'),
]
