from django.urls import path
from . import views

app_name = 'lockerApp'

urlpatterns = [
    path('', views.locker_login_view, name='login'),
 
    path('dashboard/', views.locker_dashboard_view, name='dashboard'),
    path('download/<int:file_id>/', views.download_locker_file, name='download_file'),
]
 