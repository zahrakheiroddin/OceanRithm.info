from django.urls import path
from . import views

app_name = 'jenkins'

urlpatterns = [
    path('', views.jenkins_dashboard, name='jenkins_dashboard'),
    path('jenkins-config-linux/', views.jenkins_config_linux, name='jenkins_config_linux'),
    path('jenkins-config-mac/', views.jenkins_config_mac, name='jenkins_config_mac'),
    path('jenkins-config-windows/', views.jenkins_config_windows, name='jenkins_config_windows'),
    
    # Status check endpoints
    path('check-jenkins-status-linux/', views.check_jenkins_status_linux, name='check_jenkins_status_linux'),
    path('check-jenkins-status-mac/', views.check_jenkins_status, name='check_jenkins_status_mac'),
    path('check-jenkins-status-windows/', views.check_jenkins_status_windows, name='check_jenkins_status_windows'),
    
    # Installation endpoints
    path('install-jenkins-ubuntu-package/', views.install_jenkins_ubuntu_package, name='install_jenkins_ubuntu_package'),
    path('install-jenkins-ubuntu-docker/', views.install_jenkins_ubuntu_docker, name='install_jenkins_ubuntu_docker'),
]
