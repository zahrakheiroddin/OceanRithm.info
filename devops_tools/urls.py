from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core import views as core_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    # github actions urls
    path('githubaction/', include('githubaction.urls')),
    # jenkins urls
    path('jenkins/', include('jenkins.urls', namespace='jenkins')),
    # Authentication URLs
    path('signup/', core_views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='repository/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    

]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 




    