from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('predict/', views.prediction_form, name='predict'),
    path('history/', views.history, name='history'),
    path('profile/', views.profile, name='profile'),
    path('edit_prediction/<int:prediction_id>/', views.edit_prediction, name='edit_prediction'),
]
