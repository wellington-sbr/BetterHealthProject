

from django.conf.urls.static import static
from django.urls import path
from BetterHealthProject import settings
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('home/', views.home, name='home'),
    path('appointments/', views.appointments_view, name='appointments'),
    path('settings/', views.settings_view, name='settings'),
    path('contact/', views.contact_view, name='contact'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
