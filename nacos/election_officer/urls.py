from django.urls import path
from . import views

app_name = 'election_officer'

urlpatterns = [
    path('login/', views.officer_login, name='officer_login'),
    path('logout/', views.officer_logout, name='officer_logout'),
    path('dashboard/', views.officer_dashboard, name='officer_dashboard'),  # Ensure this line exists
    path('update-timeline/', views.update_election_timeline, name='update_election_timeline'),
    path('manage-application/', views.manage_contest_application, name='manage_contest_application'),
]