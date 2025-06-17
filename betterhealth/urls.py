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
    path('admin-calendar/', views.admin_calendar, name='calendar_admin'),
    path('citas-json/', views.citas_json, name='citas_json'),
    path('register-staff/', views.register_staff, name='register_staff'),
    path('admin-panel/', views.admin_panel, name='panel_administrativo'),

    path('listado_facturas/', views.listado_facturas, name='listado_facturas'),
    path('panel-finanzas/', views.finances_panel, name='panel_finanzas'),
    path('detalle_cita_admin/<int:cita_id>/', views.detalle_cita_admin, name='detalle_cita_admin'),
    path('cita/<int:cita_id>/confirmar/', views.confirmar_cita, name='confirmar_cita'),
    path('cita/<int:cita_id>/cancelar/', views.cancelar_cita, name='cancelar_cita'),
    path('cita/<int:cita_id>/reprogramar/', views.reprogramar_cita, name='reprogramar_cita'),
    path("staff/import-services/", views.import_services_view, name="import_services"),
    path("staff/add-service/", views.add_service_view, name="add_service"),
    path("staff/delete-service/<int:service_id>/", views.delete_service_view, name="delete_service"),
    path("staff/export-services/", views.export_services_csv, name="export_services_csv"),
    path('cita/<int:cita_id>/invoice/', views.generar_factura, name='generar_factura'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
