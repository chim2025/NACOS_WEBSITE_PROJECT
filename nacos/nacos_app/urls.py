from django.urls import path
from . import views
app_name = 'nacos_app'

urlpatterns = [  # Changed from url_patterns to urlpatterns
    path('login/', views.login_view, name='login'),
    path('set-password/', views.set_password_view, name='set_password'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('check-session/', views.check_session, name='check_session'),
    path('upload-profile-picture/', views.upload_profile_picture, name='upload_profile_picture'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
]