from django.urls import path
from . import views
app_name = 'nacos_app'

urlpatterns = [  
    path('login/', views.login_view, name='login'),
    path('set-password/', views.set_password_view, name='set_password'),
   
    path('dashboard/', views.dashboard_view, name='student_dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('check-session/', views.check_session, name='check_session'),
    path('upload-profile-picture/', views.upload_profile_picture, name='upload_profile_picture'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    
    path('api/positions/', views.get_positions_api, name='get_positions_api'),
    path('submit-contest/', views.submit_contest_application, name='submit_contest_application'),
    path('api/contest-status/', views.check_contest_status, name='check_contest_status'),
    
    
    path('mark-message-read/<int:message_id>/', views.mark_message_read, name='mark_message_read'),
    path('ajax/mark-message-read/', views.ajax_mark_message_read, name='ajax_mark_message_read'),
    path('api/latest-timeline/', views.get_latest_timeline, name='get_latest_timeline'),
    path('api/election-data/', views.get_election_data, name='get_election_data'),
    path('api/submit-vote/', views.submit_vote, name='submit_vote'),
    # urls.py
    path('live-results/', views.get_live_results, name='get_live_results'),
    
]