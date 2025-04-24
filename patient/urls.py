

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

    path('settings/', views.settings_view, name='settings'),
    path('contact/', views.contact_view, name='contact'),
    path('programar-cita/', views.programar_cita, name='programar_cita'),
    path('mis-citas/', views.mis_citas, name='mis_citas'),
    path('cita/<int:cita_id>/', views.detalle_cita, name='detalle_cita'),
    path('accounts/login/', views.login_view, name='login'),

    path('cita/<int:cita_id>/cancelar/', views.cancelar_cita, name='cancelar_cita'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
