from django.urls import path
from django.http import JsonResponse
from . import views

app_name = 'election_officer'

urlpatterns = [
    path('login/', views.officer_login, name='officer_login'),
    path('logout/', views.officer_logout, name='officer_logout'),
    path('dashboard/', views.officer_dashboard, name='officer_dashboard'),  # Ensure this line exists
    path('update-timeline/', views.update_election_timeline, name='update_election_timeline'),
    path('manage-application/', views.manage_contest_application, name='manage_contest_application'),
    path('notifications/', views.officer_notifications, name='officer_notifications'),
    path('positions/create/', views.create_position, name='create_position'),
    path('positions/', views.get_positions, name='get_positions'),
    path('live/', views.election_live, name='election_live'),
    path('api/latest-timeline/', views.get_latest_timeline, name='get_latest_timeline'),
    path('api/applications/', views.get_applications_api, name='get_applications_api'),
    path('api/approve/<int:app_id>/', views.approve_application, name='approve_application'),
    path('api/reject/<int:app_id>/', views.reject_application, name='reject_application'),
   
    path('timeline/delete/<int:pk>/', views.delete_timeline, name='delete_timeline'),
    
    
   
    path('timeline/delete-base/', lambda request: JsonResponse({'success': False}), name='delete_timeline_base'),
    
    path('position/delete/<int:pk>/', views.delete_position, name='delete_position'),
    # nacos_app/urls.py
    path('api/students/', views.get_students_api, name='get_students_api'),
]