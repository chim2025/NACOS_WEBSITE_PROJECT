"""
URL configuration for nacos project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""




from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from nacos_app.views import login_view, admin_login_view, set_password_view, dashboard_view
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from nacos_app import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('set-password/', views.set_password_view, name='set_password'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('check-session/', views.check_session, name='check_session'),
    path('admin/', admin.site.urls),
    
    path('upload-profile-picture/', views.upload_profile_picture, name='upload_profile_picture'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('', lambda request: redirect('login'), name='home'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
