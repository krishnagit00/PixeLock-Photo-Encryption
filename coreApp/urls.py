from django.urls import path
from . import views

# 1. THIS WAS MISSING: It tells Django that "coreApp:..." refers to this file
app_name = 'coreApp' 

urlpatterns = [
    # 2. FIXED: Changed 'views.history' to 'views.history_view' to match your views.py
    path('history/', views.history_view, name='history'),

    # 3. This is your feedback form
    path('submit-feedback/', views.submit_feedback, name='submit_feedback'),
]