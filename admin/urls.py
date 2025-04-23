from django.urls import path
from . import views
from .views import AdminLoginView

urlpatterns = [
    path('login/', AdminLoginView.as_view(), name='login'),
    path('', views.AdminCalendarView.as_view(), name='dashboard'),

]