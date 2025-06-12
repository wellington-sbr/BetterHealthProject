from .models import Service, PatientProfile, Cita, StaffProfile, Invoice
from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.utils.html import format_html

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type', 'price', 'included_in_mutual', 'duration_minutes', 'requires_mutual_authorization')

    def import_csv_link(self, request):
        return redirect('/staff/import-services/')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-services/', self.import_csv_link, name='import_services'),
        ]
        return custom_urls + urls

    def import_csv_button(self, obj):
        return format_html('<a class="button" href="/staff/import-services/">Importar CSV</a>')

    import_csv_button.short_description = "Importar Servicios desde CSV"
